# -*- coding: utf-8 -*-
"""實驗 2：產生一天（1440 分鐘）的訂單服務指標，含日常雜訊與當天埋入的事故。放在受治理 repo 之外：種子固定，讀得到原始碼就算得出未來每天的事故（2026-10-05 移出）。

指標（每分鐘一筆）：
  p95_latency_ms   請求延遲 p95
  error_rate       5xx 每分鐘筆數
  http_409_rate    409（已出貨不可取消，屬正常業務）每分鐘筆數
  queue_depth      通知佇列深度
  heap_mb          記憶體
  notify_failed    每分鐘通知送失敗數
  receipts_gap     累計「服務計為已送出」減「接收端收據」——大於 0 代表有通知沒真的送到

事故類型（每天依種子挑 2–3 個，時間隨機）：
  sink_down          接收端掛掉 15–30 分鐘：notify_failed 上升、queue 堆積、receipts_gap 上升
  memory_leak        記憶體在 60–120 分鐘內線性上升到 > 400
  latency_regression p95 持續 > 300 達 20–40 分鐘
  silent_drop        通知被默默丟棄 20–40 分鐘：receipts_gap 上升，但沒有任何失敗訊號

  python simulate.py --day 1     # 輸出 .data/day01/{metrics.json,truth.json}
"""
from pathlib import Path
import argparse, json, random

ROOT = Path(__file__).resolve().parent
# 秘密鹽只存在本資料夾：repo 的 git 歷史裡有舊版 simulate.py，沒有鹽就算不出事故（2026-10-05）
SALT = (ROOT / '.salt').read_text().strip()
KINDS = ['sink_down', 'memory_leak', 'latency_regression', 'silent_drop']


def day_series(day):
    rng = random.Random(f'loop-lab-exp2-{SALT}-{day}')
    n = 1440
    m = {k: [0.0] * n for k in ('p95_latency_ms', 'error_rate', 'http_409_rate', 'queue_depth', 'heap_mb', 'notify_failed', 'receipts_gap')}
    gap = 0.0
    for t in range(n):
        # 日常雜訊
        m['p95_latency_ms'][t] = rng.gauss(60, 8) + (rng.random() < 0.02) * rng.uniform(150, 260)   # 偶發 1 分鐘尖峰
        m['error_rate'][t] = 1.0 if rng.random() < 0.01 else 0.0                                     # 偶發單筆 5xx
        m['http_409_rate'][t] = max(0, rng.gauss(2, 1.5)) + (rng.random() < 0.03) * rng.uniform(4, 9)  # 業務正常的 409
        m['queue_depth'][t] = max(0, rng.gauss(2, 1.5)) + (rng.random() < 0.03) * rng.uniform(10, 25)  # 短暫爆量
        m['heap_mb'][t] = 70 + 60 * ((t % 37) / 37)                                                     # GC 鋸齒 70–130
        m['notify_failed'][t] = 1.0 if rng.random() < 0.005 else 0.0
    incidents = []
    for kind in rng.sample(KINDS, rng.choice([2, 3])):
        if kind == 'sink_down':
            dur = rng.randint(15, 30)
        elif kind == 'memory_leak':
            dur = rng.randint(60, 120)
        else:
            dur = rng.randint(20, 40)
        start = rng.randint(60, n - dur - 60)
        while any(not (start + dur + 30 < i['start'] or start > i['end'] + 30) for i in incidents):
            start = rng.randint(60, n - dur - 60)
        incidents.append({'kind': kind, 'start': start, 'end': start + dur})
    for inc in incidents:
        s, e, k = inc['start'], inc['end'], inc['kind']
        for t in range(s, e):
            f = (t - s) / max(1, e - s)
            if k == 'sink_down':
                m['notify_failed'][t] = rng.uniform(8, 15)
                m['queue_depth'][t] = 20 + 200 * f
            elif k == 'memory_leak':
                m['heap_mb'][t] = 130 + 300 * f + rng.gauss(0, 5)
            elif k == 'latency_regression':
                m['p95_latency_ms'][t] = rng.uniform(300, 420)
            elif k == 'silent_drop':
                pass
    for t in range(n):
        dropping = any(i['kind'] in ('silent_drop', 'sink_down') and i['start'] <= t < i['end'] for i in incidents)
        gap += rng.uniform(3, 6) if dropping else -min(gap, rng.uniform(4, 8)) * (0 if any(i['kind'] == 'silent_drop' and i['start'] <= t < i['end'] + 20 for i in incidents) else 1)
        m['receipts_gap'][t] = max(0.0, gap)
    for k in m:
        m[k] = [round(v, 2) for v in m[k]]
    return m, sorted(incidents, key=lambda i: i['start'])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--day', type=int, required=True); a = ap.parse_args()
    m, inc = day_series(a.day)
    out = ROOT / '.data' / f'day{a.day:02d}'; out.mkdir(parents=True, exist_ok=True)
    (out / 'metrics.json').write_text(json.dumps(m), encoding='utf-8')
    (out / 'truth.json').write_text(json.dumps({'day': a.day, 'incidents': inc}, indent=2), encoding='utf-8')
    print(f'day{a.day:02d}: {len(inc)} incidents -> {out}')


if __name__ == '__main__':
    main()
