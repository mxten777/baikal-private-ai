import sys, requests, time
if sys.platform=='win32':
    sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.post('http://localhost/api/auth/login', json={'username':'admin','password':'Baikal@2026!'}, timeout=10)
docs = s.get('http://localhost/api/documents', timeout=10).json()
proc = [d for d in docs if d['status']!='completed']
if not proc:
    print('모두 완료'); raise SystemExit(0)
d = proc[0]
print(f"대기: {d['filename']}")
t0 = time.time()
while time.time()-t0 < 600:
    r = s.get(f"http://localhost/api/documents/{d['id']}/status", timeout=10).json()
    el = int(time.time()-t0)
    print(f"[{el:3d}s] {r['status']} total={r.get('total_chunks')} processed={r.get('processed_chunks')}")
    if r['status'] in ('completed','failed'):
        if r.get('error_message'): print('err:', r['error_message'][:120])
        break
    time.sleep(10)
