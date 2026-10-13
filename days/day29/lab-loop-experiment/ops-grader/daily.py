# -*- coding: utf-8 -*-
"""實驗 2 的外層每日作業（放在受治理 repo 之外，agent 看不到出題與答案）。

  python daily.py --day N [--repo C:/<AUTHOR>/loop-lab/order-service]

1. 產生第 N 天的指標與答案（.data/dayNN/，留在本資料夾）
2. 把當天 metrics.json 放進 repo 的 ops/data/dayNN/（agent 可看）
3. 用 repo main 上目前的 ops/alerts/rules.yml 評分，成績單寫進 repo 的 ops/scores/dayNN.json：
   雜訊數、每條規則的觸發／有效／雜訊、漏報了哪種事故（事後檢討等級，不含事故時間窗）
4. 在 repo commit 一次（只動 ops/data 與 ops/scores）
"""
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent

ap = argparse.ArgumentParser(); ap.add_argument('--day', type=int); ap.add_argument('--auto', action='store_true')
ap.add_argument('--repo', default=r'C:\<AUTHOR>\loop-lab\order-service'); a = ap.parse_args()
if a.auto:
    import datetime as _dt
    a.day = (_dt.date.today() - _dt.date(2026, 10, 5)).days + 1   # 10-05＝第 1 天（開跑前基準）
    if (Path(a.repo) / 'ops' / 'scores' / f'day{a.day:02d}.json').exists():
        print(f'day{a.day:02d} 已存在，略過'); sys.exit(0)
if not a.day:
    ap.error('需要 --day N 或 --auto')
repo = Path(a.repo); tag = f'day{a.day:02d}'
env = {**os.environ, 'OPS_RULES': str(repo / 'ops' / 'alerts' / 'rules.yml'), 'PYTHONUTF8': '1'}
subprocess.run([sys.executable, str(HERE / 'simulate.py'), '--day', str(a.day)], check=True, env=env)
subprocess.run([sys.executable, str(HERE / 'evaluate.py'), '--day', str(a.day)], check=True, env=env, capture_output=True)
d = HERE / '.data' / tag
(repo / 'ops' / 'data' / tag).mkdir(parents=True, exist_ok=True)
shutil.copy2(d / 'metrics.json', repo / 'ops' / 'data' / tag / 'metrics.json')
ev = json.loads((d / 'eval.json').read_text(encoding='utf-8'))
score = {'day': a.day, 'rules': ev['rules'], 'page_noise': ev['page_noise'], 'ticket_noise': ev['ticket_noise'],
         'incidents': ev['incidents'], 'missed': ev['missed'], 'per_rule': ev['per_rule'],
         'note': '外層評分（評分程式與答案不在本 repo）；missed 只列事故種類，不含時間窗'}
(repo / 'ops' / 'scores').mkdir(parents=True, exist_ok=True)
(repo / 'ops' / 'scores' / f'{tag}.json').write_text(json.dumps(score, ensure_ascii=False, indent=2), encoding='utf-8')
g = lambda *x: subprocess.run(['git', *x], cwd=repo, capture_output=True, text=True)
g('add', 'ops/data', 'ops/scores')
g('-c', 'user.name=ops-grader', '-c', 'user.email=g@local', 'commit', '-qm', f'ops: {tag} 指標與成績單（外層評分）')
print(json.dumps({k: score[k] for k in ('day', 'page_noise', 'ticket_noise', 'incidents', 'missed')}, ensure_ascii=False))
