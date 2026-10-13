# -*- coding: utf-8 -*-
"""實驗 3 的外層每日 Eval（放在受治理 repo 之外）。

  python skill_daily.py --auto | --day N [--repo C:/<AUTHOR>/loop-lab/order-service]

在 repo main 上跑一次 skill-lab/eval.py（9 題 × 2 次，約 US$2.1），成績單寫進 skill-lab/scores/dayNN.json 並 commit。
Eval 會另外呼叫 18 次 claude，不受 LoopDeck 單輪上限管，所以由外層每天固定跑一次、另外記帳；
迴圈組與對照組只讀成績單，不自己跑（2026-10-05 決定）。
"""
from pathlib import Path
import argparse, datetime as dt, json, os, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
ap = argparse.ArgumentParser(); ap.add_argument('--day', type=int); ap.add_argument('--auto', action='store_true')
ap.add_argument('--repo', default='C:/<AUTHOR>/loop-lab/order-service'); a = ap.parse_args()
repo = Path(a.repo)
if a.auto:
    a.day = (dt.date.today() - dt.date(2026, 10, 5)).days + 1
if not a.day:
    ap.error('需要 --day N 或 --auto')
tag = f'day{a.day:02d}'; out = repo / 'skill-lab' / 'scores' / f'{tag}.json'
if out.exists():
    print(f'{tag} 已存在，略過'); sys.exit(0)
g = lambda *x: subprocess.run(['git', *x], cwd=repo, capture_output=True, text=True, encoding='utf-8', errors='replace')
head = g('rev-parse', '--short', 'HEAD').stdout.strip()
EV = Path(__file__).resolve().parent / 'skill-eval'   # 考題、正解、eval.py 都在外層（2026-10-05 移出 repo）
r = subprocess.run([sys.executable, str(EV / 'eval.py'), '--reps', '2', '--label', f'grader-{tag}'], cwd=str(EV),
                   capture_output=True, text=True, encoding='utf-8', errors='replace',
                   env={**os.environ, 'PYTHONUTF8': '1', 'SKILL_DIR': str(repo / 'skill-lab' / 'skill' / '.claude')})
runs = sorted((EV / '.runs').glob(f'grader-{tag}-*/summary.json'))
if not runs:
    print('eval 沒有產出 summary：', r.stderr[-500:]); sys.exit(1)
s = json.loads(runs[-1].read_text(encoding='utf-8'))
# 成績單只用匿名編號：題目名稱本身就是提示（例如 h3-receipt-before-cancel）
names = sorted({row['case'] for row in s['rows']}); anon = {n: f'c{i:02d}' for i, n in enumerate(names, 1)}
cases = {}
for row in s['rows']:
    c = cases.setdefault(anon[row['case']], {'semantic': 0, 'contract': 0, 'runs': 0})
    c['semantic'] += row['semantic_ok']; c['contract'] += row['contract_ok']; c['runs'] += 1
score = {'day': a.day, 'commit': head, 'skill_version': s['skill_version'], 'semantic_ok': s['semantic_ok'],
         'contract_ok': s['contract_ok'], 'runs': s['runs'], 'cost_usd': s['cost_usd'], 'per_case': cases,
         'note': '外層每日 Eval（main 上目前的 skill-lab/skill/）；考題與正解不在 repo，題目以匿名編號表示'}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(score, ensure_ascii=False, indent=2), encoding='utf-8')
g('add', str(out.relative_to(repo)))
g('-c', 'user.name=ops-grader', '-c', 'user.email=g@local', 'commit', '-qm', f'skill-lab: {tag} 外層 Eval 成績單（v{s["skill_version"]}，語意 {s["semantic_ok"]}/{s["runs"]}）')
print(json.dumps({k: score[k] for k in ('day', 'skill_version', 'semantic_ok', 'contract_ok', 'runs', 'cost_usd')}, ensure_ascii=False))
