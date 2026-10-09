"""Grade Claude's reconcile.py against claude-criteria.md. Fixtures are created only here, after the run."""
from pathlib import Path
import json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent
w = ROOT/(sys.argv[1] if len(sys.argv) > 1 else (ROOT/'latest-claude-run.txt').read_text().strip())
script = w/'reconcile.py'
B = 'missing-notification-20260921-193835'
fx_root = w/'_grading'
if fx_root.exists(): shutil.rmtree(fx_root)
fx_root.mkdir()

def run(dirs, tag):
    out = fx_root/('out-'+tag)
    p = subprocess.run([sys.executable, str(script), *map(str, dirs), '--out', str(out)], capture_output=True, text=True, encoding='utf-8', timeout=120)
    try: return json.loads((out/'view.json').read_text(encoding='utf-8-sig')), p
    except Exception as e: return None, p

def rows(view): return view if isinstance(view, list) else view.get('runs', view.get('rows', [])) if isinstance(view, dict) else []
def jl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def wjl(p, rs): p.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rs), encoding='utf-8')

results = []
def rec(name, ok, got): results.append({'name': name, 'passed': bool(ok), 'got': got})

# A. real runs
data = sorted((w/'data').iterdir())
view, p = run(data, 'real')
R = {r.get('run_id'): r for r in rows(view)} if view else {}
def g(rid): return next((r for k, r in R.items() if k and rid in str(k)), {})
a, b, c = g('193704'), g('193835'), g('slow-sync')
pick = lambda r: {k: r.get(k) for k in ('expected', 'received', 'unmatched', 'status')}
unm_a = [e for e in a.get('events', []) if str(e.get('state', '')).lower() not in ('matched', 'received', 'completed', 'done')]
rec('A1 original 9/3 investigate +6 events', a.get('expected') == 9 and a.get('received') == 3 and a.get('status') == 'investigate' and len(unm_a) == 6, {**pick(a), 'unmatched_events': len(unm_a)})
rec('A2 fixed 9/9 matched', b.get('expected') == 9 and b.get('received') == 9 and b.get('status') == 'matched', pick(b))
rec('A3 slow 259/12 unknown', c.get('expected') == 259 and c.get('received') == 12 and c.get('status') == 'unknown', pick(c))

# B. hidden fixtures built from the fixed run
src = w/'data'/B
def fixture(tag, mutate):
    d = fx_root/('fx-'+tag); shutil.copytree(src, d); mutate(d)
    v, _ = run([d], tag); r = rows(v)[0] if v and rows(v) else {}
    return pick(r)
def no_receipts(d): (d/'receipts.jsonl').unlink()
def wrong_ids(d): wjl(d/'receipts.jsonl', [{**r, 'notification_id': 'wrong-'+str(r.get('notification_id'))} for r in jl(d/'receipts.jsonl')])
def dup(d): rs = jl(d/'receipts.jsonl'); wjl(d/'receipts.jsonl', rs+[rs[0]])
def no_ids(d): wjl(d/'logs.jsonl', [r for r in jl(d/'logs.jsonl') if not r.get('notification_id')])
def unfinished(d):
    m = json.loads((d/'manifest.json').read_text(encoding='utf-8-sig')); m['wait'] = {}; m['status'] = 'running'; m['last_queue_depth'] = 6
    (d/'manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')
    t = (d/'metrics.txt').read_text(encoding='utf-8-sig')
    import re; t = re.sub(r'^(oc_\w*queue_depth\S*)\s+[\d.]+', r'\1 6', t, flags=re.M)
    (d/'metrics.txt').write_text(t, encoding='utf-8'); wjl(d/'receipts.jsonl', jl(d/'receipts.jsonl')[:3])
r1 = fixture('no-receipts', no_receipts); rec('B1 missing receiver file -> null/unknown', r1.get('received') is None and r1.get('status') == 'unknown', r1)
r2 = fixture('wrong-ids', wrong_ids); rec('B2 same count wrong ids -> 0/investigate', r2.get('received') == 0 and r2.get('status') == 'investigate', r2)
r3 = fixture('duplicate', dup); rec('B3 duplicate receipt -> still 9', r3.get('received') == 9, r3)
r4 = fixture('no-sender-ids', no_ids); rec('B4 sender lacks notification id -> unknown', r4.get('status') == 'unknown', r4)
r5 = fixture('unfinished', unfinished); rec('B5 unfinished window -> waiting', r5.get('status') == 'waiting', r5)

A = sum(r['passed'] for r in results[:3]); Bn = sum(r['passed'] for r in results[3:])
verdict = '成立' if A == 3 and Bn >= 4 else '有價值的失敗' if c.get('status') == 'investigate' else '方向對、仍需人補' if A >= 2 or Bn >= 2 else '未達'
out = {'A_passed': A, 'B_passed': Bn, 'verdict': verdict, 'results': results}
(w/'grading.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(out, ensure_ascii=False, indent=2))
