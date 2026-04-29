"""실패 문서 자동 복구
- '서버 재시작으로 인해 처리가 중단' → retry 엔드포인트
- 그 외 (Bad offset / No /Root object 등 파일 부패) → 삭제 후 demo_docs/law 에서 동명 파일 재업로드
"""
import sys, os, requests, time
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost'
DEMO_DIRS = ['demo_docs/law', 'demo_docs']

s = requests.Session()
s.post(f'{BASE}/api/auth/login', json={'username':'admin','password':'Baikal@2026!'}, timeout=10).raise_for_status()

def find_local(filename: str):
    for d in DEMO_DIRS:
        p = os.path.join(d, filename)
        if os.path.isfile(p):
            return p
    return None

def mime_for(name: str):
    ext = name.rsplit('.', 1)[-1].lower()
    return {
        'pdf': 'application/pdf',
        'hwpx': 'application/vnd.hancom.hwpx',
        'hwp': 'application/x-hwp',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }.get(ext, 'application/octet-stream')

def wait_done(doc_id: str, timeout: int = 600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = s.get(f'{BASE}/api/documents/{doc_id}/status', timeout=10).json()
        st = r['status']
        el = int(time.time() - t0)
        print(f"   [{el:3d}s] {st} total={r.get('total_chunks')} processed={r.get('processed_chunks')}")
        if st in ('completed', 'failed'):
            return st, r.get('error_message')
        time.sleep(5)
    return 'timeout', None

docs = s.get(f'{BASE}/api/documents', timeout=10).json()
failed = [d for d in docs if d['status'] == 'failed']
print(f"실패 문서 {len(failed)}건:\n")

for d in failed:
    name = d['filename']
    err = d.get('error_message') or ''
    print(f"▶ {name}")
    print(f"  에러: {err[:80]}")

    if '서버 재시작' in err or '중단' in err:
        # retry로 복구
        print("  → retry 엔드포인트 호출")
        r = s.post(f"{BASE}/api/documents/{d['id']}/retry", timeout=30)
        if r.status_code != 200:
            print(f"  [SKIP] retry 실패: {r.status_code} {r.text[:100]}")
            continue
        st, msg = wait_done(d['id'])
        print(f"  결과: {st}" + (f" ({msg[:80]})" if msg else ""))
    else:
        # 파일 부패 → 삭제 후 재업로드
        local = find_local(name)
        if not local:
            print(f"  [SKIP] 로컬 원본 없음 ({DEMO_DIRS})")
            continue
        print(f"  → 삭제 후 재업로드 ({local})")
        s.delete(f"{BASE}/api/documents/{d['id']}", timeout=10)
        with open(local, 'rb') as f:
            r = s.post(f'{BASE}/api/documents/upload',
                       files={'file': (name, f, mime_for(name))}, timeout=120)
        if r.status_code != 201:
            print(f"  [SKIP] 업로드 실패: {r.status_code} {r.text[:100]}")
            continue
        new_id = r.json()['id']
        st, msg = wait_done(new_id)
        print(f"  결과: {st}" + (f" ({msg[:80]})" if msg else ""))
    print()

print("=== 최종 상태 ===")
docs = s.get(f'{BASE}/api/documents', timeout=10).json()
for d in docs:
    if d['status'] != 'completed':
        print(f"  [{d['status']}] {d['filename']}")
print(f"completed: {sum(1 for d in docs if d['status']=='completed')}/{len(docs)}")
