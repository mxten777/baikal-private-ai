"""
법령 데모 5건 색인 후 eval_testset_law.json 의 placeholder를 실제 UUID로 채운다.

전제:
  - BAIKAL 백엔드가 기동 중 (기본: http://localhost/api 또는 http://localhost:8000)
  - 관리자 계정으로 데모 5건이 업로드/완료된 상태

사용법:
  python scripts/fill_law_testset_ids.py \
      --api http://localhost/api \
      --user admin --password ****** \
      --testset scripts/eval_testset_law.json

매핑 규칙 (파일명 부분 일치, 첫 매칭 우선):
  DOC1_PUBLIC_INFO_LAW          → "정보공개" AND "법률"
  DOC2_ADMIN_PROCEDURE          → "행정절차"
  DOC3_STANDARD_INFO_ORDINANCE  → "정보공개" AND "조례"
  DOC4_STANDARD_DUTY_ORDINANCE  → "복무" AND "조례"
  DOC5_HR_GUIDELINE             → "복무" 또는 "징계" 또는 "예규" (위 4건과 다른 것)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

PLACEHOLDER_RULES = {
    "DOC1_PUBLIC_INFO_LAW":          [["정보공개", "법률"]],
    "DOC2_ADMIN_PROCEDURE":          [["행정절차"]],
    "DOC3_STANDARD_INFO_ORDINANCE":  [["정보공개", "조례"], ["정보공개", "표준"]],
    "DOC4_STANDARD_DUTY_ORDINANCE":  [["복무", "조례"], ["복무", "표준"]],
    "DOC5_HR_GUIDELINE":             [["예규"], ["지침"], ["징계"], ["인사"]],
}


def login(api: str, user: str, password: str) -> str:
    r = requests.post(f"{api}/auth/login", json={"username": user, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def list_documents(api: str, token: str) -> list[dict]:
    r = requests.get(f"{api}/documents", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data


def match_doc(filename: str, rules: list[list[str]]) -> bool:
    for rule in rules:
        if all(kw in filename for kw in rule):
            return True
    return False


def resolve_placeholders(documents: list[dict]) -> dict:
    """placeholder → document_id 매핑."""
    mapping = {}
    used_ids = set()
    for placeholder, rules in PLACEHOLDER_RULES.items():
        for doc in documents:
            doc_id = doc.get("id") or doc.get("document_id")
            filename = doc.get("filename") or doc.get("name") or ""
            if doc_id in used_ids:
                continue
            if match_doc(filename, rules):
                mapping[placeholder] = doc_id
                used_ids.add(doc_id)
                break
    return mapping


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost/api")
    parser.add_argument("--user", default="admin")
    parser.add_argument("--password", required=True)
    parser.add_argument("--testset", default="scripts/eval_testset_law.json")
    parser.add_argument("--output", default=None,
                        help="결과 저장 경로 (생략 시 입력 파일 덮어쓰기)")
    parser.add_argument("--dry-run", action="store_true",
                        help="매핑만 출력, 파일 갱신 안 함")
    args = parser.parse_args()

    print(f"[1/4] 로그인: {args.api}")
    try:
        token = login(args.api, args.user, args.password)
    except requests.HTTPError as e:
        print(f"  ❌ 로그인 실패: {e}")
        sys.exit(1)

    print("[2/4] 문서 목록 조회")
    docs = list_documents(args.api, token)
    print(f"  → {len(docs)}건")

    print("[3/4] placeholder → document_id 매핑")
    mapping = resolve_placeholders(docs)
    for ph, did in mapping.items():
        fn = next((d.get("filename") or d.get("name", "") for d in docs
                   if (d.get("id") or d.get("document_id")) == did), "?")
        print(f"  {ph:35} → {did}  ({fn})")
    missing = [ph for ph in PLACEHOLDER_RULES if ph not in mapping]
    for ph in missing:
        print(f"  ⚠️  매칭 실패: {ph}")
    if missing:
        print("\n  업로드된 파일명 목록:")
        for d in docs:
            print(f"    - {d.get('filename') or d.get('name', '?')}")
        print("\n  파일명에 위 키워드가 포함되어 있는지 확인 후 재실행.")

    if args.dry_run:
        print("[4/4] dry-run, 파일 갱신 생략")
        return

    if missing:
        print("\n  매칭 실패 항목이 있어 갱신을 중단합니다. --dry-run 으로 먼저 확인하세요.")
        sys.exit(2)

    print("[4/4] 테스트셋 갱신")
    src = Path(args.testset)
    data = json.loads(src.read_text(encoding="utf-8"))
    for item in data:
        ids = item.get("relevant_doc_ids", [])
        item["relevant_doc_ids"] = [mapping.get(x, x) for x in ids]
    out_path = Path(args.output) if args.output else src
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  저장: {out_path}")


if __name__ == "__main__":
    main()
