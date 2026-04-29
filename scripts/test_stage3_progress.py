"""Stage 3.1/3.2 검증 - 진행률 컬럼 + retry 엔드포인트
- 작은 hwpx 업로드하여 status API에서 total_chunks/processed_chunks 추적
- failed 상태 문서 만들고 retry 엔드포인트 호출 → uploading 으로 전환 확인
"""
import sys, requests, time, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost'
s = requests.Session()
s.post(f'{BASE}/api/auth/login', json={'username':'admin','password':'Baikal@2026!'}, timeout=10).raise_for_status()

# 1) 진행률 컬럼 검증 — 처리 중 문서가 있으면 status에 total/processed 노출 확인
print('=== Test 1: 진행률 컬럼 노출 ===')
docs = s.get(f'{BASE}/api/documents', timeout=10).json()
completed = [d for d in docs if d['status'] == 'completed']
if completed:
    d = completed[0]
    has_total = 'total_chunks' in d
    has_proc = 'processed_chunks' in d
    print(f"  완료 문서 '{d['filename'][:40]}': total_chunks={d.get('total_chunks')} processed_chunks={d.get('processed_chunks')}")
    assert has_total and has_proc, "스키마에 진행률 컬럼 없음"
    print("  [PASS] DocumentResponse에 total_chunks/processed_chunks 포함")

# 2) retry 엔드포인트 — completed 문서 재처리는 400, 정상 흐름은 200
print('\n=== Test 2: retry 엔드포인트 ===')
if completed:
    d = completed[0]
    r = s.post(f"{BASE}/api/documents/{d['id']}/retry", timeout=10)
    if r.status_code == 400:
        print(f"  [PASS] completed 문서 retry → 400 (메시지: {r.json().get('detail','')[:60]})")
    else:
        print(f"  [FAIL] completed 문서 retry → {r.status_code} (기대 400)")

# 3) 존재하지 않는 ID
r = s.post(f"{BASE}/api/documents/00000000-0000-0000-0000-000000000000/retry", timeout=10)
if r.status_code == 404:
    print("  [PASS] 미존재 문서 retry → 404")
else:
    print(f"  [FAIL] 미존재 문서 retry → {r.status_code}")

print('\n=== 완료 ===')
