# -*- coding: utf-8 -*-
"""對一個 run 目錄評估 slo/rules.json，輸出 slo-report.json。

用法：python slo/check_slo.py evidence/runs/<run-id> [...]
只讀 run 目錄，不重跑服務。
"""
import io, os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(io.open(os.path.join(HERE, 'rules.json'), encoding='utf-8'))


def jsonl(p):
    if not os.path.exists(p):
        return []
    out = []
    for line in io.open(p, encoding='utf-8-sig'):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def parse_metrics(p):
    """Prometheus 文字格式 → {name: value}、{le: cumulative}"""
    flat, buckets = {}, {}
    if not os.path.exists(p):
        return flat, buckets
    for line in io.open(p, encoding='utf-8-sig'):
        m = re.match(r'^([a-zA-Z_][\w]*)(\{[^}]*\})?\s+([0-9.eE+-]+)\s*$', line.strip())
        if not m:
            continue
        name, labels, val = m.group(1), m.group(2) or '', float(m.group(3))
        if name == 'oc_request_latency_ms_bucket':
            le = re.search(r'le="([^"]+)"', labels)
            if le:
                buckets[le.group(1)] = val
        else:
            flat[name + labels] = val
    return flat, buckets


def pct(sorted_vals, q):
    if not sorted_vals:
        return None
    i = min(len(sorted_vals) - 1, max(0, int(round(q * len(sorted_vals))) - 1))
    return round(sorted_vals[i], 1)


def hist_quantile(buckets, total, q):
    """Prometheus histogram_quantile 的線性內插，和 Grafana 畫的是同一條。"""
    if not buckets or not total:
        return None, None
    edges = sorted(((float('inf') if k == '+Inf' else float(k)), v) for k, v in buckets.items())
    target = q * total
    prev_edge, prev_cum = 0.0, 0.0
    for edge, cum in edges:
        if cum >= target:
            if edge == float('inf'):
                return None, prev_edge
            frac = 0.0 if cum == prev_cum else (target - prev_cum) / (cum - prev_cum)
            return round(prev_edge + (edge - prev_edge) * frac, 2), edge
        prev_edge, prev_cum = edge, cum
    return None, None


def evaluate(run_dir):
    rid = os.path.basename(os.path.normpath(run_dir))
    man = {}
    mp = os.path.join(run_dir, 'manifest.json')
    if os.path.exists(mp):
        man = json.load(io.open(mp, encoding='utf-8-sig'))
    reqs = jsonl(os.path.join(run_dir, 'requests.jsonl'))
    receipts = jsonl(os.path.join(run_dir, 'receipts.jsonl'))
    tl = jsonl(os.path.join(run_dir, 'metrics-timeline.jsonl'))
    flat, buckets = parse_metrics(os.path.join(run_dir, 'metrics.txt'))

    lat = sorted(r['client_latency_ms'] for r in reqs
                 if isinstance(r.get('client_latency_ms'), (int, float)))
    statuses = [r.get('http_status') for r in reqs]
    allowed = {200, 409, 404, 401}
    n = len(statuses)

    transitions = flat.get('oc_transitions_total')
    uniq = len({r.get('notification_id') for r in receipts}) if receipts else 0

    heaps = [t.get('oc_gc_heap_bytes') for t in tl if t.get('oc_gc_heap_bytes')]
    growth_mb = round((heaps[-1] - heaps[0]) / 1048576.0, 1) if len(heaps) >= 2 else None

    findings, worst = [], 'ok'
    order = {'ok': 0, 'unknown': 1, 'alert': 2, 'freeze': 3, 'page': 4}
    mode = man.get('mode') or 'functional'
    depth = flat.get('oc_notify_queue_depth')

    def add(sli, ok, detail, unknown=False):
        nonlocal worst
        applies = sli.get('applies_to', {}).get('manifest.mode')
        if applies and mode != applies:
            lvl, detail = 'n/a', detail + '｜本情境 mode=%s，本條不適用' % mode
        elif unknown:
            lvl, detail = 'unknown', detail + '｜訊號不存在，不判違反'
        else:
            lvl = 'ok' if ok else sli['on_breach']
        if order.get(lvl, 0) > order[worst]:
            worst = lvl
        findings.append({'id': sli['id'], 'name': sli['name'], 'source': sli['source'],
                         'level': lvl, 'detail': detail})

    by = {s: statuses.count(s) for s in set(statuses)}
    for s in RULES['slis']:
        if s['id'] == 'SLI-01':
            bad = [s2 for s2 in statuses if s2 not in allowed]
            add(s, not bad and n > 0, '%d 筆請求，狀態分布 %s，規格外狀態 %d 筆' % (n, by, len(bad)))
        elif s['id'] == 'SLI-02':
            base = '轉換 %s／唯一收據 %d' % (transitions, uniq)
            if transitions is None:
                add(s, False, base, unknown=True)
            elif s.get('precondition') and depth not in (0, None) and depth > 0:
                add(s, False, base + '；run 結束時佇列深度 %s，未排空' % depth, unknown=True)
            else:
                add(s, uniq == transitions, base)
        elif s['id'] == 'SLI-03':
            p95 = pct(lat, 0.95)
            add(s, p95 is not None and p95 <= s['threshold']['max_ms'],
                '客戶端 p95=%s ms（門檻 %s）' % (p95, s['threshold']['max_ms']),
                unknown=(p95 is None))
        elif s['id'] == 'SLI-04':
            add(s, growth_mb is not None and growth_mb <= s['threshold']['max_mb'],
                'heap 成長 %s MB（門檻 %s，%d 個取樣）' % (growth_mb, s['threshold']['max_mb'], len(heaps)),
                unknown=(growth_mb is None))
        elif s['id'] == 'SLI-05':
            drained = bool((man.get('wait') or {}).get('terminal'))
            base = 'run 結束時佇列深度 %s' % depth
            if depth is None:
                add(s, False, base, unknown=True)
            elif s.get('precondition', {}).get('run_confirmed_drained') and not drained and depth > 0:
                add(s, False, base + '；本 run 未以 wait.terminal 確認排空', unknown=True)
            else:
                add(s, depth <= s['threshold']['max'], base)

    total = flat.get('oc_request_latency_ms_count')
    h50, _ = hist_quantile(buckets, total, 0.5)
    h95, _ = hist_quantile(buckets, total, 0.95)
    c50, c95 = pct(lat, 0.5), pct(lat, 0.95)
    first_edge = min((float(k) for k in buckets if k != '+Inf'), default=None)
    first_cum = buckets.get(str(int(first_edge)) if first_edge and first_edge == int(first_edge)
                            else str(first_edge)) if first_edge is not None else None
    in_first = round(100.0 * first_cum / total, 2) if first_cum and total else None

    return {
        'run_id': rid, 'version': man.get('version'), 'scenario': man.get('scenario'),
        'mode': mode,
        'rules_version': RULES['version'], 'verdict': worst, 'findings': findings,
        'dashboard_vs_client': {
            'histogram_p50_ms': h50, 'client_p50_ms': c50,
            'histogram_p95_ms': h95, 'client_p95_ms': c95,
            'first_bucket_le_ms': first_edge, 'pct_samples_in_first_bucket': in_first,
            'note': ('伺服器直方圖與客戶端量到的是不同東西：直方圖只含 handler 內部，'
                     '客戶端含連線、排隊與序列化。落在第一個桶裡的比例越高，'
                     'histogram_quantile 的結果越接近純內插。'),
        },
    }


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    reports = [evaluate(a) for a in args]
    for r in reports:
        out = os.path.join([a for a in args][reports.index(r)], 'slo-report.json')
        json.dump(r, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    lines = []
    for r in reports:
        lines.append('%-36s %-9s %s' % (r['run_id'], r['verdict'],
                     ' | '.join('%s:%s' % (f['id'], f['level']) for f in r['findings'])))
    io.open(os.path.join(HERE, 'last-check.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
    print('wrote %d slo-report.json' % len(reports))
