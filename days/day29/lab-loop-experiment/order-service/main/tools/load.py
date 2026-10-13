# -*- coding: utf-8 -*-
"""負載產生器（壓力測試）：建 N 張訂單，再以固定併發送取消請求；每筆帶 X-Request-Id／X-Run-Id／X-Actor，
可附固定大小的 JSON payload（模擬「取消原因附件」）。客戶端每筆記一行 requests.jsonl（含客戶端量到的 latency）。
只用標準庫。用法：python tools/load.py --api http://127.0.0.1:5080 --run-id R --out runs/R --orders 300 --concurrency 32 --payload-bytes 32768 --repeat 3"""
import argparse, json, io, os, sys, time, threading, queue, urllib.request, urllib.error, random

def post(url, body, headers, timeout=30):
    data = body.encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, method='POST')
    for k, v in headers.items(): req.add_header(k, v)
    if data is not None: req.add_header('Content-Type', 'application/json')
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace'), (time.perf_counter() - t0) * 1000
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), (time.perf_counter() - t0) * 1000
    except Exception as e:
        return 0, type(e).__name__, (time.perf_counter() - t0) * 1000

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--api', required=True); ap.add_argument('--run-id', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--orders', type=int, default=200); ap.add_argument('--concurrency', type=int, default=16)
    ap.add_argument('--payload-bytes', type=int, default=0); ap.add_argument('--repeat', type=int, default=1, help='每張訂單取消幾次（>1 產生重複取消）')
    ap.add_argument('--seed', type=int, default=7); ap.add_argument('--paid-ratio', type=float, default=0.5); ap.add_argument('--shipped-ratio', type=float, default=0.1)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    os.makedirs(a.out, exist_ok=True)
    reqlog = io.open(os.path.join(a.out, 'requests.jsonl'), 'a', encoding='utf-8', newline='\n'); lock = threading.Lock()
    hdr = {'X-Run-Id': a.run_id}
    orders = []
    for i in range(a.orders):
        oid = 'L-%05d' % i; shipped = rnd.random() < a.shipped_ratio; paid = rnd.random() < a.paid_ratio
        orders.append((oid, shipped, paid))
        st, _, _ = post(a.api + '/orders', json.dumps({'id': oid, 'shipped': shipped, 'paid': paid}), hdr)
        if st != 200: print('create failed', oid, st, file=sys.stderr); sys.exit(2)
    note = ('x' * a.payload_bytes) if a.payload_bytes > 0 else None
    jobs = queue.Queue()
    seq = 0
    for rep in range(a.repeat):
        for oid, _, _ in orders:
            seq += 1; jobs.put((seq, oid, rep))
    total = seq; counts = {}; stopped = threading.Event(); t_start = time.perf_counter()
    def worker():
        while not stopped.is_set():
            try: s, oid, rep = jobs.get_nowait()
            except queue.Empty: return
            rid = '%s-r%05d' % (a.run_id[:12], s)
            body = json.dumps({'reason': 'load-test', 'note': note}) if note else None
            st, resp, lat = post(a.api + '/orders/%s/cancel' % oid, body, {'X-Request-Id': rid, 'X-Run-Id': a.run_id, 'X-Actor': 'loadgen'})
            rec = {'seq': s, 'request_id': rid, 'run_id': a.run_id, 'op': 'cancel', 'order_id': oid, 'repeat': rep, 'http_status': st, 'client_latency_ms': round(lat, 1), 'response': resp[:200], 'sent_at': time.strftime('%Y-%m-%dT%H:%M:%S')}
            with lock:
                counts[st] = counts.get(st, 0) + 1
                reqlog.write(json.dumps(rec, ensure_ascii=False) + '\n')
            if st == 0: stopped.set()   # 連線斷了（服務掛了）就全部停
    ts = [threading.Thread(target=worker, daemon=True) for _ in range(a.concurrency)]
    for t in ts: t.start()
    for t in ts: t.join()
    reqlog.close()
    summary = {'orders': a.orders, 'repeat': a.repeat, 'total_requests': total, 'completed': sum(counts.values()), 'by_status': counts, 'concurrency': a.concurrency, 'payload_bytes': a.payload_bytes, 'elapsed_s': round(time.perf_counter() - t_start, 2), 'aborted_on_connection_error': stopped.is_set()}
    io.open(os.path.join(a.out, 'load-summary.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False))
    return 0

if __name__ == '__main__': sys.exit(main())
