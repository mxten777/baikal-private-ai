import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('scripts/q20_full_baseline.json', encoding='utf-8'))
print('=== SUMMARY ===')
print(json.dumps(d['summary'], ensure_ascii=False, indent=2))
print('\n=== A GROUP ALL ===')
for r in d['results']:
    if r['group'] == 'A':
        st = 'PASS' if r['pass'] else 'FAIL'
        det = r.get('details', {})
        print(f"\nQ{r['id']:02d} [{st}] {r['elapsed_s']:.1f}s conf={det.get('confidence')} {r['question']}")
        if not r['pass']:
            print(f"  reasons: {r.get('reasons')}")
            ap = det.get('answer_preview','')
            print(f"  answer: {ap[:300]}")
            print(f"  sources: {det.get('sources',[])}")
