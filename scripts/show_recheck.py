import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('scripts/q20_recheck_78.json', encoding='utf-8'))
for r in d['results']:
    status = 'PASS' if r['pass'] else 'FAIL'
    qid = r['id']
    elapsed = r['elapsed_s']
    conf = r['details'].get('confidence')
    print(f"Q{qid:02d} [{status}] {elapsed}s conf={conf}")
    if not r['pass']:
        print(f"  reasons: {r['reasons']}")
    srcs = r['details'].get('sources')
    preview = r['details'].get('answer_preview', '')[:150]
    print(f"  sources: {srcs}")
    print(f"  preview: {preview}")
