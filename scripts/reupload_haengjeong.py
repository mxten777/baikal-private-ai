"""법령 hwpx 재업로드 - 깨끗한 multipart 사용"""
import sys, requests, time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost'
s = requests.Session()
s.post(f'{BASE}/api/auth/login', json={'username':'admin','password':'Baikal@2026!'}, timeout=10).raise_for_status()

# 기존 동명 삭제
docs = s.get(f'{BASE}/api/documents', timeout=10).json()
for d in docs:
    if '행정절차' in d['filename']:
        r = s.delete(f"{BASE}/api/documents/{d['id']}", timeout=10)
        print(f"  deleted: {d['filename']} → {r.status_code}")

# 업로드
fp = r'demo_docs/law/행정절차법(법률)(제18748호)(20230324).hwpx'
fname = '행정절차법(법률)(제18748호)(20230324).hwpx'
with open(fp, 'rb') as f:
    r = s.post(f'{BASE}/api/documents/upload',
               files={'file': (fname, f, 'application/vnd.hancom.hwpx')},
               timeout=60)
print('upload status:', r.status_code)
data = r.json()
doc_id = data['id']
print('doc_id:', doc_id)

# 폴링
t0 = time.time()
while True:
    rr = s.get(f'{BASE}/api/documents/{doc_id}/status', timeout=10).json()
    el = int(time.time() - t0)
    print(f'  [{el:3d}s] status={rr["status"]} total={rr.get("total_chunks")} processed={rr.get("processed_chunks")}')
    if rr['status'] in ('completed', 'failed'):
        if rr['status'] == 'failed':
            print('  ERROR:', rr.get('error_message'))
        break
    if el > 300:
        print('  TIMEOUT'); break
    time.sleep(5)
