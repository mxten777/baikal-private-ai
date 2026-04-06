"""
BAIKAL Private AI - API 종합 테스트
실행: python scripts/api_test.py
의존: pip install httpx
"""
import sys
import json
import time
import httpx

BASE = "http://localhost:8000"
TIMEOUT = 30.0
ADMIN_PW = "Baikal@2026!"  # .env DEFAULT_ADMIN_PASSWORD

PASS = "OK"
FAIL = "NG"
WARN = "WARN"

results = []

def check(label: str, ok: bool, detail: str = ""):
    icon = PASS if ok else FAIL
    msg = f"[{icon}] {label}"
    if detail:
        msg += f"\n      {detail}"
    print(msg)
    results.append((label, ok))
    return ok

def section(title: str):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


# 1. 헬스체크
section("1. 서버 헬스체크")
try:
    r = httpx.get(f"{BASE}/api/health", timeout=10.0)
    check("GET /api/health -> 200", r.status_code == 200, r.text[:120])
except Exception as e:
    check("GET /api/health -> 연결 가능", False, str(e))
    print("\n서버에 연결할 수 없습니다.")
    sys.exit(1)


# 2. 인증
section("2. 인증 (로그인)")

r = httpx.post(f"{BASE}/api/auth/login",
    json={"username": "admin", "password": ADMIN_PW}, timeout=TIMEOUT)
admin_ok = check("POST /api/auth/login (admin) -> 200", r.status_code == 200,
    f"status={r.status_code}")
login_resp = r.json() if admin_ok else {}
admin_token = login_resp.get("access_token")
refresh_token_val = login_resp.get("refresh_token")

r = httpx.post(f"{BASE}/api/auth/login",
    json={"username": "admin", "password": "wrongpass"}, timeout=TIMEOUT)
check("로그인 실패 (잘못된 비밀번호) -> 401", r.status_code == 401,
    f"status={r.status_code}")

if refresh_token_val:
    r = httpx.post(f"{BASE}/api/auth/refresh",
        json={"refresh_token": refresh_token_val}, timeout=TIMEOUT)
    check("POST /api/auth/refresh -> 200", r.status_code == 200,
        f"status={r.status_code}")
else:
    print(f"  [{WARN}] refresh_token 없음 (로그인 응답에 refresh_token 필드 없음)")

admin_h = {"Authorization": f"Bearer {admin_token}"}


# 3. 사용자 관리
section("3. 사용자 관리 (admin)")

r = httpx.get(f"{BASE}/api/users", headers=admin_h, timeout=TIMEOUT)
check("GET /api/users (admin) -> 200", r.status_code == 200,
    f"users={len(r.json()) if r.status_code==200 else r.text[:80]}")

ts = str(int(time.time()))
r = httpx.post(f"{BASE}/api/users",
    headers=admin_h,
    json={"username": f"testuser_{ts}", "password": "Test1234!", "role": "user"},
    timeout=TIMEOUT)
test_user_ok = check("POST /api/users (create user) -> 201", r.status_code == 201,
    f"status={r.status_code}")
test_user_id = r.json().get("id") if test_user_ok else None

user_h = {}
if test_user_ok:
    r = httpx.post(f"{BASE}/api/auth/login",
        json={"username": f"testuser_{ts}", "password": "Test1234!"}, timeout=TIMEOUT)
    user_ok = check("테스트 유저 로그인 -> 200", r.status_code == 200)
    user_token = r.json().get("access_token") if user_ok else None
    if user_token:
        user_h = {"Authorization": f"Bearer {user_token}"}


# 4. 문서 목록
section("4. 문서 목록 조회")

r = httpx.get(f"{BASE}/api/documents", headers=admin_h, timeout=TIMEOUT)
check("GET /api/documents (admin) -> 200", r.status_code == 200,
    f"docs={len(r.json()) if r.status_code==200 else r.text[:80]}")

docs = r.json() if r.status_code == 200 else []
completed_docs = [d for d in docs if d.get("status") == "completed"]
first_doc_id = completed_docs[0]["id"] if completed_docs else None
print(f"      완료된 문서: {len(completed_docs)}개")

if first_doc_id and user_h:
    r = httpx.get(f"{BASE}/api/documents/{first_doc_id}/status",
        headers=user_h, timeout=TIMEOUT)
    check("IDOR 방지: 타인 문서 상태 조회 -> 403", r.status_code == 403,
        f"status={r.status_code} (403이어야 보안 정상)")

r = httpx.get(f"{BASE}/api/documents", timeout=TIMEOUT)
check("GET /api/documents (비인증) -> 401/403", r.status_code in (401, 403),
    f"status={r.status_code}")


# 5. 문서 업로드
section("5. 문서 업로드")

# 유효한 최소 PDF (외부 라이브러리 불필요)
pdf_bytes = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 52>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (BAIKAL API Test PDF) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000266 00000 n \n"
    b"0000000370 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n9\n%%EOF"
)

r = httpx.post(f"{BASE}/api/documents/upload",
    headers=admin_h,
    files={"file": ("api_test.pdf", pdf_bytes, "application/pdf")},
    data={"allowed_roles": '["admin","manager","user"]'},
    timeout=60.0)
upload_ok = check("POST /api/documents/upload -> 200/201",
    r.status_code in (200, 201),
    f"status={r.status_code}  {r.text[:120]}")
upload_doc_id = r.json().get("id") if upload_ok else None

if upload_doc_id:
    print("      문서 처리 대기 중 (최대 30초)...")
    for i in range(15):
        time.sleep(2)
        r2 = httpx.get(f"{BASE}/api/documents/{upload_doc_id}/status",
            headers=admin_h, timeout=TIMEOUT)
        if r2.status_code == 200:
            st = r2.json().get("status")
            if st == "completed":
                check(f"문서 처리 완료 ({(i+1)*2}초)", True, f"status={st}")
                break
            elif st == "failed":
                check("문서 처리", False,
                    f"error={r2.json().get('error_message', '')}")
                break
    else:
        print(f"  [{WARN}] 처리 시간 초과 (아직 processing 중일 수 있음)")


# 6. 검색
section("6. 문서 검색")

r = httpx.get(f"{BASE}/api/search?q=BAIKAL&mode=hybrid",
    headers=admin_h, timeout=TIMEOUT)
check("GET /api/search?q=BAIKAL (hybrid) -> 200", r.status_code == 200,
    f"results={len(r.json()) if r.status_code==200 else r.text[:80]}")

r = httpx.get(f"{BASE}/api/search?q=문서&mode=vector",
    headers=admin_h, timeout=TIMEOUT)
check("GET /api/search?q=문서 (vector) -> 200", r.status_code == 200,
    f"status={r.status_code}")

r = httpx.get(f"{BASE}/api/search?q=규정&mode=keyword",
    headers=admin_h, timeout=TIMEOUT)
check("GET /api/search?q=규정 (keyword) -> 200", r.status_code == 200,
    f"status={r.status_code}")


# 7. 채팅 세션 & 질의응답
section("7. 채팅 세션 및 질의응답")

r = httpx.post(f"{BASE}/api/chat/sessions",
    headers=admin_h, json={}, timeout=TIMEOUT)
session_ok = check("POST /api/chat/sessions -> 201",
    r.status_code in (200, 201), f"status={r.status_code}")
session_id = r.json().get("id") if session_ok else None

r = httpx.get(f"{BASE}/api/chat/sessions", headers=admin_h, timeout=TIMEOUT)
check("GET /api/chat/sessions -> 200", r.status_code == 200,
    f"sessions={len(r.json()) if r.status_code==200 else r.text[:60]}")

if session_id and completed_docs:
    try:
        print("      LLM 질의 중 (최대 3분)...")
        r = httpx.post(f"{BASE}/api/chat/ask",
            headers=admin_h,
            json={
                "question": "BAIKAL Private AI의 주요 장점은?",
                "session_id": session_id,
            },
            timeout=180.0)
        ask_ok = check("POST /api/chat/ask -> 200", r.status_code == 200,
            f"status={r.status_code}")
        if ask_ok:
            data = r.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            confidence = data.get("confidence_score", 0)
            check("질의응답: 답변 있음", bool(answer), f"len={len(answer)}자")
            check("질의응답: 출처 있음", bool(sources), f"sources={len(sources)}개")
            check("질의응답: 신뢰도 점수", confidence > 0, f"score={confidence}")
            print(f"      답변: {answer[:120]}...")
    except httpx.TimeoutException:
        print(f"  [{WARN}] LLM 응답 타임아웃 (180초) - Ollama 모델 로딩 중일 수 있음")
    except Exception as e:
        check("POST /api/chat/ask", False, str(e)[:80])


# 8. 스트리밍 질의응답
section("8. 스트리밍 질의응답")

if session_id and completed_docs:
    try:
        print("      스트리밍 LLM 질의 중 (최대 3분)...")
        r = httpx.post(f"{BASE}/api/chat/ask/stream",
            headers=admin_h,
            json={
                "question": "폐쇄망에서 사용할 수 있는 이유를 설명해줘",
                "session_id": session_id,
            },
            timeout=180.0)
        check("POST /api/chat/ask/stream -> 200", r.status_code == 200,
            f"status={r.status_code}")
        if r.status_code == 200:
            lines = [l for l in r.text.split("\n") if l.startswith("data:")]
            types = set()
            for line in lines:
                try:
                    d = json.loads(line[5:])
                    types.add(d.get("type"))
                except Exception:
                    pass
            check("스트리밍: sources 이벤트", "sources" in types, f"types={types}")
            check("스트리밍: token 이벤트", "token" in types, f"types={types}")
            check("스트리밍: done 이벤트", "done" in types, f"types={types}")
    except httpx.TimeoutException:
        print(f"  [{WARN}] 스트리밍 LLM 타임아웃")
    except Exception as e:
        check("POST /api/chat/ask/stream", False, str(e)[:80])


# 9. 감사 로그
section("9. 감사 로그")

r = httpx.get(f"{BASE}/api/admin/query-logs", headers=admin_h, timeout=TIMEOUT)
check("GET /api/admin/query-logs (admin) -> 200", r.status_code == 200,
    f"logs={len(r.json()) if r.status_code==200 else r.text[:80]}")

if user_h:
    r = httpx.get(f"{BASE}/api/admin/query-logs", headers=user_h, timeout=TIMEOUT)
    check("감사 로그 접근 제어: user -> 403", r.status_code == 403,
        f"status={r.status_code}")


# 10. 정리
section("10. 테스트 데이터 정리")

if upload_doc_id:
    r = httpx.delete(f"{BASE}/api/documents/{upload_doc_id}",
        headers=admin_h, timeout=TIMEOUT)
    check("테스트 문서 삭제", r.status_code in (200, 204),
        f"status={r.status_code}")

if test_user_id:
    r = httpx.delete(f"{BASE}/api/users/{test_user_id}",
        headers=admin_h, timeout=TIMEOUT)
    check("테스트 유저 삭제", r.status_code in (200, 204),
        f"status={r.status_code}")


# 최종 결과
section("테스트 결과 요약")
total = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed
print(f"\n  전체: {total}개  |  [{PASS}] 통과: {passed}개  |  [{FAIL}] 실패: {failed}개")

if failed:
    print(f"\n  실패 항목:")
    for label, ok in results:
        if not ok:
            print(f"    [{FAIL}] {label}")

print()
sys.exit(0 if failed == 0 else 1)
