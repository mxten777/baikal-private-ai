"""
Stage 2.4 — 시연 질문 20개 자동 평가 (baseline 측정)

채점 규칙:
  A/B/C 그룹 (답변 기대): 다음 모두 충족 시 PASS
    - HTTP 200, refusal_reason 없음
    - confidence_score >= min_confidence
    - 답변 텍스트에 expected_keywords 중 min_keyword_matches 개 이상 포함
    - sources 중 1건 이상이 expected_source_pattern (정규식) 일치
  D 그룹 (거절 기대): 다음 중 하나라도 충족 시 PASS
    - refusal_reason 가 None 이 아님
    - confidence_score < 0.40
    - 답변에 표준 거절 문구가 포함됨

사용:
  python scripts/eval_demo_q20.py
  python scripts/eval_demo_q20.py --testset scripts/demo_q20_testset.json --out scripts/eval_q20_result.json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

BASE_URL = "http://localhost"
ADMIN_USER = "admin"
ADMIN_PASS = "Baikal@2026!"

REFUSAL_PHRASES = [
    "관련도가 낮아",
    "답변을 생성하지 않습니다",
    "확인되지 않습니다",
    "찾을 수 없",
]


def login(session: requests.Session) -> None:
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10,
    )
    r.raise_for_status()


def create_session(session: requests.Session, title: str) -> str:
    r = session.post(
        f"{BASE_URL}/api/chat/sessions",
        json={"title": title},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["id"]


def delete_session(session: requests.Session, sid: str) -> None:
    try:
        session.delete(f"{BASE_URL}/api/chat/sessions/{sid}", timeout=10)
    except Exception:
        pass


def ask(session: requests.Session, sid: str, question: str, timeout: int = 180) -> dict:
    r = session.post(
        f"{BASE_URL}/api/chat/ask",
        json={"session_id": sid, "question": question},
        timeout=timeout,
    )
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "body": r.text[:200]}
    return r.json()


def grade(q: dict, resp: dict) -> dict:
    """반환: {pass: bool, reasons: [str], details: dict}"""
    reasons = []
    is_pass = True

    # D 그룹: guardrail에 의한 HTTP 400 차단도 정상 거절로 인정
    if "error" in resp:
        if q.get("expect_refusal") and "HTTP 400" in resp["error"]:
            return {
                "pass": True,
                "reasons": ["guardrail_blocked"],
                "details": {
                    "answer_len": 0,
                    "answer_preview": resp.get("body", "")[:200],
                    "confidence": 0.0,
                    "refusal_reason": "guardrail",
                    "source_count": 0,
                    "sources": [],
                },
            }
        return {"pass": False, "reasons": [resp["error"]], "details": resp}

    answer = resp.get("answer") or ""
    sources = resp.get("sources") or []
    confidence = resp.get("confidence_score") or 0.0
    refusal = resp.get("refusal_reason")

    if q.get("expect_refusal"):
        # D 그룹: 거절 기대
        refused_explicit = bool(refusal)
        refused_low_conf = confidence < 0.40
        refused_phrase = any(p in answer for p in REFUSAL_PHRASES)
        if not (refused_explicit or refused_low_conf or refused_phrase):
            is_pass = False
            reasons.append(
                f"거절되어야 함 (confidence={confidence:.2f}, refusal={refusal})"
            )
        return {
            "pass": is_pass,
            "reasons": reasons,
            "details": {
                "answer_len": len(answer),
                "answer_preview": answer[:200],
                "confidence": confidence,
                "refusal_reason": refusal,
                "source_count": len(sources),
                "sources": [s.get("filename") for s in sources][:3],
            },
        }

    # A/B/C 그룹: 답변 기대
    if refusal:
        is_pass = False
        reasons.append(f"refusal_reason={refusal}")

    min_conf = q.get("min_confidence", 0.40)
    if confidence < min_conf:
        is_pass = False
        reasons.append(f"confidence {confidence:.2f} < {min_conf}")

    keywords = q.get("expected_keywords") or []
    min_matches = q.get("min_keyword_matches", 0)
    matched = [k for k in keywords if k in answer]
    if len(matched) < min_matches:
        is_pass = False
        reasons.append(
            f"키워드 매치 {len(matched)}/{min_matches} (필요 {min_matches}+ / 매칭: {matched})"
        )

    src_pattern = q.get("expected_source_pattern")
    if src_pattern:
        matched_src = [
            s.get("filename", "")
            for s in sources
            if re.search(src_pattern, s.get("filename") or "")
        ]
        if not matched_src:
            is_pass = False
            reasons.append(f"출처 패턴 '{src_pattern}' 미매치")

    return {
        "pass": is_pass,
        "reasons": reasons,
        "details": {
            "answer_len": len(answer),
            "answer_preview": answer[:120],
            "confidence": confidence,
            "matched_keywords": matched,
            "sources": [s.get("filename") for s in sources][:3],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--testset", default="scripts/demo_q20_testset.json")
    parser.add_argument("--out", default="scripts/eval_q20_result.json")
    parser.add_argument("--ids", default="", help="쉼표 구분 ID만 실행 (예: 1,3,16)")
    args = parser.parse_args()

    testset_path = Path(args.testset)
    questions = json.loads(testset_path.read_text(encoding="utf-8"))["questions"]
    if args.ids:
        wanted = {int(x) for x in args.ids.split(",")}
        questions = [q for q in questions if q["id"] in wanted]

    s = requests.Session()
    login(s)

    results = []
    group_stats: dict[str, dict[str, int]] = {}
    sid = create_session(s, f"Q20 평가 {time.strftime('%Y%m%d-%H%M%S')}")

    try:
        for q in questions:
            print(f"\n[Q{q['id']:02d} {q['group']}] {q['question']}")
            t0 = time.time()
            try:
                resp = ask(s, sid, q["question"], timeout=180)
            except requests.exceptions.RequestException as e:
                resp = {"error": str(e)}
            elapsed = round(time.time() - t0, 1)
            r = grade(q, resp)
            tag = "PASS" if r["pass"] else "FAIL"
            print(f"  [{tag}] {elapsed}s — {'; '.join(r['reasons']) if r['reasons'] else 'OK'}")
            d = r["details"]
            if "answer_preview" in d:
                print(f"    answer: {d['answer_preview']!r}")
                print(f"    confidence={d['confidence']:.3f}, sources={d['sources']}")
            else:
                print(f"    confidence={d.get('confidence', 0):.3f}, refusal={d.get('refusal_reason')}")
            results.append({"id": q["id"], "group": q["group"], "question": q["question"], "elapsed_s": elapsed, **r})
            grp = group_stats.setdefault(q["group"], {"pass": 0, "fail": 0})
            grp["pass" if r["pass"] else "fail"] += 1
    finally:
        delete_session(s, sid)

    # 종합
    print("\n" + "=" * 60)
    print(" Stage 2 baseline — 그룹별 결과")
    print("=" * 60)
    total_pass = total_fail = 0
    thresholds = {"A": (7, 8), "B": (4, 4), "C": (2, 3), "D": (4, 5)}
    for grp in sorted(group_stats.keys()):
        st = group_stats[grp]
        n = st["pass"] + st["fail"]
        threshold, group_total = thresholds.get(grp, (0, n))
        verdict = "✅" if st["pass"] >= threshold else "❌"
        print(f"  {grp}: {st['pass']}/{n} (합격선 {threshold}/{group_total}) {verdict}")
        total_pass += st["pass"]
        total_fail += st["fail"]
    overall = "✅ 합격" if total_pass >= 14 else "❌ 미달"
    print(f"\n  TOTAL: {total_pass}/{total_pass + total_fail} (합격선 14/20) {overall}")

    out_path = Path(args.out)
    out_path.write_text(
        json.dumps(
            {
                "summary": {
                    "total_pass": total_pass,
                    "total_fail": total_fail,
                    "by_group": group_stats,
                },
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n  결과 저장: {out_path}")
    return 0 if total_pass >= 14 else 1


if __name__ == "__main__":
    sys.exit(main())
