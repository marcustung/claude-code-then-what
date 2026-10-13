# -*- coding: utf-8 -*-
"""壓力情境 checker：服務活著且所有請求都有回應、p95 在門檻內、記憶體沒有單向成長、通知對帳成立 → PASS。
崩潰（status=crashed）、timeout、連線中斷、p95 超門檻、heap 成長超門檻 → FAIL。門檻寫在 scenario.expected。
用法：python tools/check-load.py evidence/runs/<run_id>"""
import io, json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

def jsonl(p):
    if not os.path.exists(p): return None
    out = []
    for line in io.open(p, encoding='utf-8-sig'):
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def pct(vals, q):
    if not vals: return None
    v = sorted(vals); i = min(len(v) - 1, int(round(q * (len(v) - 1)))); return v[i]

def main(run_dir):
    findings, ok = [], True
    def fail(m): nonlocal ok; ok = False; findings.append('FAIL ' + m)
    def note(m): findings.append('ok   ' + m)
    man = json.load(io.open(os.path.join(run_dir, 'manifest.json'), encoding='utf-8-sig'))
    exp = man.get('expected') or {}
    st = man.get('status')
    if st == 'crashed':
        err = ''
        ep = os.path.join(run_dir, 'api-stderr.txt')
        if os.path.exists(ep):
            lines = [l.rstrip() for l in io.open(ep, encoding='utf-8-sig', errors='replace') if l.strip()]
            err = ' | '.join(lines[:3]) if lines else ''
        fail('服務程序崩潰 exit=%s：%s' % (man.get('api_exit_code'), err[:300] or '（stderr 空）'))
    elif st != 'terminal': fail('run 未達終態：status=%s' % st)
    reqs = jsonl(os.path.join(run_dir, 'requests.jsonl')) or []
    lat = [r['client_latency_ms'] for r in reqs if isinstance(r.get('client_latency_ms'), (int, float)) and r.get('http_status') not in (0, None)]
    by = {}
    for r in reqs: by[r.get('http_status')] = by.get(r.get('http_status'), 0) + 1
    ls_p = os.path.join(run_dir, 'load-summary.json')
    ls = json.load(io.open(ls_p, encoding='utf-8-sig')) if os.path.exists(ls_p) else {}
    if ls.get('aborted_on_connection_error'): fail('負載器在連線中斷後停止：完成 %s／%s' % (ls.get('completed'), ls.get('total_requests')))
    if by.get(0): fail('%d 筆請求沒有回應（連線錯誤）' % by[0])
    p50, p95, p99 = pct(lat, .5), pct(lat, .95), pct(lat, .99)
    if p95 is not None:
        thr = exp.get('p95_ms_max')
        if thr is not None: (note if p95 <= thr else fail)('客戶端 p95=%.0f ms（門檻 %s）；p50=%.0f p99=%.0f n=%d' % (p95, thr, p50, p99, len(lat)))
        else: note('客戶端 p50/p95/p99 = %.0f/%.0f/%.0f ms n=%d' % (p50, p95, p99, len(lat)))
    tl = jsonl(os.path.join(run_dir, 'metrics-timeline.jsonl')) or []
    heap = [t.get('oc_gc_heap_bytes') for t in tl if t.get('oc_gc_heap_bytes') is not None]
    if heap:
        first, last, peak = heap[0], heap[-1], max(heap)
        growth = (last - first) / (1024 * 1024)
        thr = exp.get('heap_growth_mb_max')
        msg = 'GC heap 起 %.1f MB → 末 %.1f MB（峰 %.1f MB，%d 個取樣）' % (first / 1048576, last / 1048576, peak / 1048576, len(heap))
        if thr is not None: (note if growth <= thr else fail)(msg + '；成長 %.1f MB，門檻 %s MB' % (growth, thr))
        else: note(msg)
    else: findings.append('warn 沒有 metrics 時間線')
    # 通知對帳（活著才有意義）
    logs = jsonl(os.path.join(run_dir, 'logs.jsonl')) or []
    rcts = jsonl(os.path.join(run_dir, 'receipts.jsonl')) or []
    transitions = sum(1 for l in logs if l.get('event') == 'cancel' and l.get('transitioned') is True)
    uniq_r = len({r.get('notification_id') for r in rcts})
    if st == 'terminal':
        (note if uniq_r == transitions else fail)('通知對帳：成功轉換 %d／接收端收據 %d' % (transitions, uniq_r))
    else:
        findings.append('info 通知對帳（崩潰前）：成功轉換 %d／收據 %d' % (transitions, uniq_r))
    summary = {'status': st, 'api_exit_code': man.get('api_exit_code'), 'requests': len(reqs), 'by_status': by, 'p50_ms': p50, 'p95_ms': p95, 'p99_ms': p99,
               'heap_first_mb': round(heap[0] / 1048576, 1) if heap else None, 'heap_last_mb': round(heap[-1] / 1048576, 1) if heap else None, 'heap_peak_mb': round(max(heap) / 1048576, 1) if heap else None,
               'transitions': transitions, 'receipts_unique': uniq_r, 'load': ls, 'version': man.get('version')}
    out = {'result': 'PASS' if ok else 'FAIL', 'findings': findings, 'summary': summary}
    io.open(os.path.join(run_dir, 'check.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(out, ensure_ascii=False, indent=1))
    print('== check-load %s  %s' % (os.path.basename(run_dir), out['result']))
    for f in findings: print('  ' + f)
    return 0 if ok else 1

if __name__ == '__main__': sys.exit(main(sys.argv[1]))
