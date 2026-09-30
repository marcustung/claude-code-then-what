# -*- coding: utf-8 -*-
"""後續 取證實跑：把每一次 gcx 呼叫（指令、時間窗、回傳）完整存檔。
本腳本只負責「執行並留痕」，判斷與假設寫在 result.md，由人與 Claude 分開負責。

  python observability/gcx-investigate.py --out evidence/gcx/<run-id>
"""
import argparse, json, io, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = 'oc-local'          # 明確指定本機 context，絕不落到其他已設定的 Grafana
DS = 'oc-prometheus'


def gcx(*args):
    cmd = ['gcx', '--context', CTX] + list(args)
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    lines = [l for l in (p.stdout or '').splitlines() if l.strip()]
    payload = None
    for l in reversed(lines):                      # 最後一行才是結果，前面是 hint
        try:
            payload = json.loads(l)
            break
        except Exception:
            continue
    return {'cmd': ' '.join(cmd), 'exit': p.returncode, 'elapsed_ms': round((time.time() - t0) * 1000),
            'stdout_lines': len(lines), 'stderr': (p.stderr or '')[:400], 'parsed': payload}


def scalar(rec):
    """從 instant query 取單一數值；取不到回 None，不猜。"""
    try:
        res = rec['parsed']['data']['result']
        return float(res[0]['value'][1]) if res else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--healthy', required=True, help='RFC3339 起,迄')
    ap.add_argument('--incident', required=True)
    a = ap.parse_args()
    out = os.path.join(ROOT, a.out)
    os.makedirs(out, exist_ok=True)

    h0, h1 = a.healthy.split(',')
    i0, i1 = a.incident.split(',')

    P95 = 'histogram_quantile(0.95, sum(rate(oc_request_latency_ms_bucket[1m])) by (le))'
    P50 = 'histogram_quantile(0.50, sum(rate(oc_request_latency_ms_bucket[1m])) by (le))'
    AVG = 'sum(rate(oc_request_latency_ms_sum[1m])) / sum(rate(oc_request_latency_ms_count[1m]))'
    QD = 'max_over_time(oc_notify_queue_depth[5m])'
    ENQ = 'sum(increase(oc_notify_enqueued_total[5m]))'
    SENT = 'sum(increase(oc_notify_sent_total[5m]))'
    HEAP = 'max_over_time(oc_gc_heap_bytes[5m])'

    steps = []
    steps.append(('S1 這個 Grafana 有哪些 datasource', gcx('datasources', 'list')))
    steps.append(('S2 目標是否在線', gcx('metrics', 'query', '-d', DS, 'up{job="order-cancel-api"}')))
    steps.append(('S3 服務自報版本', gcx('metrics', 'query', '-d', DS, 'oc_info')))
    for label, t in (('healthy', h1), ('incident', i1)):
        for name, expr in (('p50', P50), ('p95', P95), ('avg', AVG), ('queue_depth', QD),
                           ('enqueued', ENQ), ('sent', SENT), ('heap', HEAP)):
            steps.append(('%s %s @%s' % (label, name, t),
                          gcx('metrics', 'query', '-d', DS, expr, '--time', t)))

    io.open(os.path.join(out, 'gcx-calls.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps([{'step': s, **r} for s, r in steps], ensure_ascii=False, indent=2))

    summary = {}
    for s, r in steps:
        v = scalar(r)
        if v is not None and (' ' in s):
            summary[s.split(' @')[0]] = v
    io.open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps({'windows': {'healthy': [h0, h1], 'incident': [i0, i1]},
                    'values': summary, 'context': CTX, 'datasource': DS},
                   ensure_ascii=False, indent=2))

    print('calls=%d  失敗=%d' % (len(steps), sum(1 for _, r in steps if r['exit'] != 0)))
    for k in sorted(summary):
        print('  %-24s %s' % (k, round(summary[k], 2)))


if __name__ == '__main__':
    main()
