"""
Stage 4.4 — 시연 전 점검 체크리스트

사용:
  python scripts/pre_demo_check.py

모든 항목 PASS 시 exit 0, 하나라도 FAIL 시 exit 1
"""
import sys
import requests

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost"
ADMIN_USER = "admin"
ADMIN_PASS = "Baikal@2026!"

REQUIRED_MODELS = ["qwen2.5:7b", "bge-m3"]
REQUIRED_DOCS_KEYWORDS = ["행정절차법", "정보공개", "공무원 임용규칙"]

results = []

def check(name, passed, detail=""):
    mark = "PASS" if passed else "FAIL"
    line = f"  [{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    results.append(passed)
    return passed


print("\n=== BAIKAL 시연 전 점검 ===\n")

# ── 1. API 헬스체크 ────────────────────────────────────────────
print("[1] 서비스 상태")
try:
    r = requests.get(f"{BASE}/api/health", timeout=8)
    data = r.json()
    check("API 응답", r.status_code == 200, f"HTTP {r.status_code}")
    check("DB 연결", data.get("components", {}).get("database") == "connected")
    check("Ollama 연결", data.get("components", {}).get("ollama") == "connected")
except Exception as e:
    check("API 응답", False, str(e))
    check("DB 연결", False, "API 미응답")
    check("Ollama 연결", False, "API 미응답")

# ── 2. 인증 ────────────────────────────────────────────────────
print("\n[2] 인증")
s = requests.Session()
try:
    r = s.post(f"{BASE}/api/auth/login", json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=8)
    check("admin 로그인", r.status_code == 200, f"HTTP {r.status_code}")
    logged_in = r.status_code == 200
except Exception as e:
    check("admin 로그인", False, str(e))
    logged_in = False

# ── 3. Ollama 모델 ─────────────────────────────────────────────
print("\n[3] Ollama 모델")
if logged_in:
    try:
        r = s.get(f"{BASE}/api/admin/models", timeout=10)
        if r.status_code == 200:
            installed = [m["name"] for m in r.json().get("models", [])]
            for model in REQUIRED_MODELS:
                found = any(model in m for m in installed)
                check(f"모델 {model}", found, f"설치됨: {[m for m in installed if model in m]}" if found else f"없음 (설치됨: {installed})")
        else:
            check("모델 목록 조회", False, f"HTTP {r.status_code}")
    except Exception as e:
        check("모델 목록 조회", False, str(e))
else:
    check("모델 확인", False, "로그인 실패로 건너뜀")

# ── 4. 문서 색인 상태 ──────────────────────────────────────────
print("\n[4] 문서 색인")
if logged_in:
    try:
        r = s.get(f"{BASE}/api/documents", timeout=10)
        if r.status_code == 200:
            docs = r.json()
            completed = [d for d in docs if d["status"] == "completed"]
            failed = [d for d in docs if d["status"] == "failed"]
            processing = [d for d in docs if d["status"] in ("processing", "uploading")]
            check("완료 문서 수", len(completed) >= 5, f"{len(completed)}건 완료")
            check("실패 문서 없음", len(failed) == 0, f"{len(failed)}건 실패" if failed else "없음")
            check("처리 중 없음", len(processing) == 0, f"{len(processing)}건 처리 중" if processing else "없음")
            # 필수 문서 키워드 확인
            for kw in REQUIRED_DOCS_KEYWORDS:
                found = any(kw in d["filename"] for d in completed)
                check(f"필수 문서: {kw}", found)
            total_chunks = sum(d.get("chunk_count") or 0 for d in completed)
            check("총 청크 수", total_chunks >= 100, f"{total_chunks:,}청크")
        else:
            check("문서 목록 조회", False, f"HTTP {r.status_code}")
    except Exception as e:
        check("문서 목록 조회", False, str(e))
else:
    check("문서 확인", False, "로그인 실패로 건너뜀")

# ── 5. RAG 응답 속도 (간이 테스트) ───────────────────────────────
print("\n[5] RAG 응답 (간이)")
if logged_in:
    try:
        # 세션 생성
        r_sess = s.post(f"{BASE}/api/chat/sessions", json={"title": "사전점검"}, timeout=10)
        if r_sess.status_code in (200, 201):
            sid = r_sess.json()["id"]
            import time
            t0 = time.time()
            try:
                r_ask = s.post(f"{BASE}/api/chat/ask",
                    json={"session_id": sid, "question": "정보공개 청구 처리 기간은?"},
                    timeout=180)
                elapsed = round(time.time() - t0, 1)
                if r_ask.status_code == 200:
                    body = r_ask.json()
                    conf = body.get("confidence_score", 0)
                    ans = body.get("answer", "")
                    check("RAG 응답 성공", True, f"{elapsed}s, confidence={conf}")
                    check("응답 시간 180s 이내", elapsed <= 180, f"{elapsed}s")
                    check("답변 비어있지 않음", bool(ans and len(ans) > 10), f"{len(ans)}자")
                else:
                    check("RAG 응답", False, f"HTTP {r_ask.status_code}")
            except BaseException as e:
                elapsed = round(time.time() - t0, 1)
                check("RAG 응답", False, f"{type(e).__name__} ({elapsed}s)")
            # 세션 정리
            try:
                s.delete(f"{BASE}/api/chat/sessions/{sid}", timeout=5)
            except Exception:
                pass
        else:
            check("세션 생성", False, f"HTTP {r_sess.status_code}")
    except Exception as e:
        check("RAG 응답", False, str(e))
else:
    check("RAG 응답 확인", False, "로그인 실패로 건너뜀")

# ── 결과 집계 ─────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'='*35}")
print(f"  결과: {passed}/{total} PASS")
if passed == total:
    print("  모든 항목 통과 — 시연 준비 완료")
else:
    fail_count = total - passed
    print(f"  {fail_count}건 실패 — 시연 전 조치 필요")
print(f"{'='*35}\n")

sys.exit(0 if passed == total else 1)
