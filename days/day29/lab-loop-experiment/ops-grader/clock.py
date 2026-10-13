# -*- coding: utf-8 -*-
"""外層時鐘：每天 01:50 跑 daily.py 與 skill_daily.py（l-02 02:20、l-03 02:40 讀當天成績單）。
與實驗引擎一起常駐；不是 Windows 工作排程，重開機需重新啟動。紀錄寫在 clock.log。"""
import datetime as dt, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
LOG = HERE / 'clock.log'
def log(m):
    with LOG.open('a', encoding='utf-8') as f: f.write(f'{dt.datetime.now():%F %T} {m}\n')
def run():
    # 實驗 2 的指標與成績單（l-02 02:20 讀），再跑實驗 3 的外層 Eval（約 10 分鐘，l-03 02:40 讀）
    for script in ('daily.py', 'skill_daily.py'):
        r = subprocess.run([sys.executable, str(HERE / script), '--auto'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        log(f'{script} exit={r.returncode} {r.stdout.strip()[-200:]} {r.stderr.strip()[-200:]}')
log('clock start')
done = None
while True:
    now = dt.datetime.now()
    if (now.hour, now.minute) >= (1, 50) and done != now.date():
        run(); done = now.date()
    time.sleep(30)
