# -*- coding: utf-8 -*-
"""Day 21 補跑：skill-lab 9 題 × 2 次，「不帶 Skill」條件。沿用鎖定的 eval.py（只讀匯入，不改檔），
唯一差別是工作目錄不放 .claude/（SKILL 指向空目錄）。輸出 summary 與 eval.py 同格式。"""
import importlib.util, json, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
EVAL = Path(r'C:\<AUTHOR>\loop-lab\order-service\skill-lab\eval.py')
spec = importlib.util.spec_from_file_location('ev', EVAL); ev = importlib.util.module_from_spec(spec)
sys.argv = ['eval.py']; spec.loader.exec_module(ev)
empty = Path(r'C:\<AUTHOR>\noskill\empty-claude'); empty.mkdir(exist_ok=True)
ev.SKILL = empty
expected = json.loads((ev.ROOT / 'expected.json').read_text(encoding='utf-8'))
out = Path(r'C:\<AUTHOR>\noskill\runs') / f"noskill-{time.strftime('%Y%m%d-%H%M%S')}"; out.mkdir(parents=True)
rows = []
for idx, case in enumerate(sorted(p.name for p in ev.CASES.iterdir() if p.is_dir()), 1):
    for rep in (1, 2):
        r = ev.run_one(case, idx, rep, out)
        exp = expected[case]
        r['semantic_ok'] = r['sender'] == exp['sender_status'] and r['receiver'] == exp['receiver_status']
        r['contract_ok'] = r['gate_exit'] == 0
        rows.append(r)
        print(f"{case:28s} rep{rep} sender={r['sender']} receiver={r['receiver']} semantic={'OK' if r['semantic_ok'] else 'NG'}", flush=True)
s = {'label': 'noskill', 'runs': len(rows), 'semantic_ok': sum(r['semantic_ok'] for r in rows),
     'contract_ok': sum(r['contract_ok'] for r in rows), 'cost_usd': round(sum(r['cost_usd'] or 0 for r in rows), 3), 'rows': rows}
(out / 'summary.json').write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"不帶 Skill：語意 {s['semantic_ok']}/{s['runs']}、契約 {s['contract_ok']}/{s['runs']}、US${s['cost_usd']}")
