# -*- coding: utf-8 -*-
"""把 k6 --out json 的原始事件，依 20 秒一段的加壓階段分桶，算每段的 p95／p99／樣本數。
用法：python analyze.py results/run-<stamp>.json
"""
import io, sys, json, bisect

STAGES = [
    (0, 20, '0→10 VU'),
    (20, 40, '10→25 VU'),
    (40, 60, '25→50 VU'),
    (60, 80, '50→100 VU'),
    (80, 100, '100→200 VU'),
    (100, 120, '200→400 VU'),
    (120, 135, '400→0 VU（收尾）'),
]


def pct(vals, q):
    if not vals:
        return None
    vals = sorted(vals)
    i = min(len(vals) - 1, max(0, int(round(q * len(vals))) - 1))
    return round(vals[i], 1)


def main():
    path = sys.argv[1]
    t0 = None
    buckets = [[] for _ in STAGES]
    n = 0
    with io.open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get('type') != 'Point':
                continue
            if e.get('metric') != 'cancel_latency_ms':
                continue
            data = e.get('data', {})
            ts = data.get('time')
            val = data.get('value')
            if ts is None or val is None:
                continue
            # k6 的 time 是 RFC3339；轉成相對秒數，第一筆當 t0
            import datetime
            tt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
            if t0 is None:
                t0 = tt
            rel = (tt - t0).total_seconds()
            for i, (a, b, _) in enumerate(STAGES):
                if a <= rel < b:
                    buckets[i].append(val)
                    break
            n += 1
    print('cancel_latency_ms 樣本總數:', n)
    print()
    print('%-16s %8s %8s %8s %8s' % ('階段', '樣本數', 'p50', 'p95', 'p99'))
    for (a, b, label), vals in zip(STAGES, buckets):
        if not vals:
            print('%-16s %8s' % (label, '（無樣本）'))
            continue
        print('%-16s %8d %8s %8s %8s' % (label, len(vals), pct(vals, 0.5), pct(vals, 0.95), pct(vals, 0.99)))
    all_over_250 = sum(1 for b in buckets for v in b if v > 250)
    print()
    print('超過 250ms 的樣本數（跨全部階段）:', all_over_250)


if __name__ == '__main__':
    main()
