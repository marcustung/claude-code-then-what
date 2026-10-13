# -*- coding: utf-8 -*-
"""外層出題：產生一天（1440 分鐘）的訂單服務指標，含日常雜訊與當天埋入的事故。
沿用 Day 29 長期實驗的模擬器（只換種子）。放在 Claude 的工作目錄之外：指標給 project/data/，事故真值只留在 grader/.truth/。

指標（每分鐘一筆）：p95_latency_ms、error_rate、http_409_rate、queue_depth、heap_mb、notify_failed、
receipts_gap（累計「服務計為已送出」減「接收端收據」，大於 0 代表有通知沒真的送到）。
事故類型（每天依種子挑 2–3 個）：sink_down、memory_leak、latency_regression、silent_drop（通知被默默丟棄，沒有任何失敗訊號）。

  python grader/simulate.py --day 1
"""
from pathlib import Path
import argparse, json, random

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
SALT = (HERE / '.salt').read_text().strip()
KINDS = ['sink_down', 'memory_leak', 'latency_regression', 'silent_drop']


def day_series(day):
    rng = random.Random(f'loop-lab-exp2-{SALT}-{day}')
    n = 1440
    m = {k: [0.0] * n for k in ('p95_latency_ms', 'error_rate', 'http_409_rate', 'queue_depth', 'heap_mb', 'notify_failed', 'receipts_gap')}
    gap = 0.0
    for t in range(n):
        m['p95_latency_ms'][t] = rng.gauss(60, 8) + (rng.random() < 0.02) * rng.uniform(150, 260)
        m['error_rate'][t] = 1.0 if rng.random() < 0.01 else 0.0
        m['http_409_rate'][t] = max(0, rng.gauss(2, 1.5)) + (rng.random() < 0.03) * rng.uniform(4, 9)
        m['queue_depth'][t] = max(0, rng.gauss(2, 1.5)) + (rng.random() < 0.03) * rng.uniform(10, 25)
        m['heap_mb'][t] = 70 + 60 * ((t % 37) / 37)
        m['notify_failed'][t] = 1.0 if rng.random() < 0.005 else 0.0
    incidents = []
    for kind in rng.sample(KINDS, rng.choice([2, 3])):
        dur = rng.randint(15, 30) if kind == 'sink_down' else rng.randint(60, 120) if kind == 'memory_leak' else rng.randint(20, 40)
        start = rng.randint(60, n - dur - 60)
        while any(not (start + dur + 30 < i['start'] or start > i['end'] + 30) for i in incidents):
            start = rng.randint(60, n - dur - 60)
        incidents.append({'kind': kind, 'start': start, 'end': start + dur})
    for inc in incidents:
        s, e, k = inc['start'], inc['end'], inc['kind']
        for t in range(s, e):
            f = (t - s) / max(1, e - s)
            if k == 'sink_down':
                m['notify_failed'][t] = rng.uniform(8, 15); m['queue_depth'][t] = 20 + 200 * f
            elif k == 'memory_leak':
                m['heap_mb'][t] = 130 + 300 * f + rng.gauss(0, 5)
            elif k == 'latency_regression':
                m['p95_latency_ms'][t] = rng.uniform(300, 420)
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
    data = KIT / 'project' / 'data' / f'day{a.day:02d}'; data.mkdir(parents=True, exist_ok=True)
    (data / 'metrics.json').write_text(json.dumps(m), encoding='utf-8')
    truth = HERE / '.truth'; truth.mkdir(exist_ok=True)
    (truth / f'day{a.day:02d}.json').write_text(json.dumps({'day': a.day, 'incidents': inc}, indent=2), encoding='utf-8')
    print(f'day{a.day:02d}: 指標 -> {data}')


if __name__ == '__main__':
    main()
