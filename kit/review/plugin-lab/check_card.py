# -*- coding: utf-8 -*-
"""Program-enforced check of a review-pr output (or a G0 baseline output).
Usage: python check_card.py <run_dir>   (reads <run_dir>/result.json extracted from trace; writes <run_dir>/check.json)
Rules (deterministic; no model):
 R1 output is one JSON object with a verdict in {PASS, NEEDS_EVIDENCE, OWNER_REQUIRED}
 R2 every finding has a non-empty source that looks like file:line, a quoted sentence, or a test name; or equals "unknown"
 R3 no finding text uses hedges: 看起來, seems, looks fine, probably, 應該沒問題
 R4 if diff.patch added lines contain gate keywords, verdict must be OWNER_REQUIRED
 R5 (skill runs) contract has 5 keys and each is filled/missing/n/a
"""
import json, re, sys, os, io
run = sys.argv[1]
def load(p):
    return io.open(p, encoding='utf-8').read()
gate_kw = re.compile(r'\b(Paid|Refund|Amount|Price|Charge|authorized|Auth|Permission|Role|DROP|DELETE FROM|migration)\b|Cancelled\s*=|Status\s*=|State\s*=')
hedge = re.compile(r'看起來|seems|looks fine|probably|應該沒問題|大概', re.I)
res = {'run': run, 'rules': {}, 'pass': True}
try:
    out = json.loads(load(os.path.join(run, 'result.json')))
    res['rules']['R1'] = out.get('verdict') in ('PASS', 'NEEDS_EVIDENCE', 'OWNER_REQUIRED')
except Exception as e:
    res['rules']['R1'] = False; res['error'] = str(e); out = {}
findings = out.get('findings', []) if isinstance(out, dict) else []
srcs = [str(f.get('source', '')).strip() for f in findings]
res['rules']['R2'] = all(s and (s == 'unknown' or re.search(r'\.\w+:\d+|"|「|Test|PASS|FAIL|PR\.md|ticket\.md|diff\.patch', s)) for s in srcs) if findings else True
res['rules']['R3'] = not any(hedge.search(json.dumps(f, ensure_ascii=False)) for f in findings)
added = '\n'.join(l[1:] for l in load(os.path.join(run, 'diff.patch')).splitlines() if l.startswith('+') and not l.startswith('+++'))
hits = sorted(set(m.group(0) for m in gate_kw.finditer(added)))
res['gate_keywords_in_diff'] = hits
res['rules']['R4'] = (out.get('verdict') == 'OWNER_REQUIRED') if hits else True
c = out.get('contract') if isinstance(out, dict) else None
res['rules']['R5'] = (isinstance(c, dict) and len(c) == 5 and all(re.match(r'(filled|missing|n/a)', str(v)) for v in c.values())) if 'skill' in out else None
res['findings'] = len(findings)
res['pass'] = all(v for v in res['rules'].values() if v is not None)
io.open(os.path.join(run, 'check.json'), 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps(res, ensure_ascii=False))
