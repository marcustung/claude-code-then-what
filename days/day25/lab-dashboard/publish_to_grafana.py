"""Send build.py's per-ID reconciliation into Day 24's local LGTM (OTLP HTTP on 127.0.0.1:4324).

Reconciliation stays in code (build.reconcile). Grafana only displays the result.
September runs are replayed with today's timestamps and labelled data_source=replay-2026-09;
Day 24's two runs are labelled data_source=day24-2026-10-07. Gauges are re-sent every interval
so Prometheus keeps a fresh sample while a dashboard is being built and rendered.

usage: python publish_to_grafana.py [--loop SECONDS] [--once]
"""
from pathlib import Path
import json, re, sys, time, urllib.request
import build

ROOT = Path(__file__).resolve().parent
EX = ROOT.parent
OTLP = 'http://127.0.0.1:4324'
D24 = EX/'day24-observability-lab/runs/20261007-050642'
# Average queue wait from Day 24's Prometheus (notification_queue_wait_milliseconds sum/count at 2026-10-06T21:07:40Z):
# day24-api-normal 323.12/9, day24-api-slow 10068.35/9.
REASON_TEXT = {'identity_reconciliation': '已逐筆核對', 'missing_notification_identity': '缺通知 ID，無法核對', 'missing_receiver_records': '缺對方收據紀錄', 'missing_sender_records': '缺系統送出紀錄', 'event_identity_incomplete': '事件識別不完整'}
# Dispatch rules are a human decision (like Day 22), published as data; the dashboard only shows them.
NEXT_STEP = {'investigate': ('查沒收到的原因', '通知服務'),
             'unknown': ('先補資料，再判斷', '資料平台'),
             'waiting': ('等處理完再看', '值班'),
             'matched': ('—', '—')}
STATUS_TEXT = {'matched': '成功', 'investigate': '失敗', 'unknown': '紀錄不全', 'waiting': '處理中'}
def impact(r):
    if r['status'] == 'investigate':
        n = r['unmatched'] or 0
        return f"{n} 位客人沒收到通知" + (f"（{r['refund_unmatched']} 位是退款）" if r.get('refund_unmatched') else '')
    if r['status'] == 'unknown':
        # Receipts that did match are still evidence; only the rest is unknown.
        return f"{r['expected']} 筆取消中，{r['unmatched']} 筆看不到通知有沒有送到"
    return '全部收到'


def summary(rows):
    """One-sentence status built by fixed rules from the reconciled rows (not by a model)."""
    bad = [r for r in rows if r['status'] == 'investigate']
    unk = [r for r in rows if r['status'] == 'unknown']
    parts = []
    for r in bad:
        parts.append(f"{r['expected']} 筆取消中，有 {impact(r)}")
    for r in unk:
        parts.append(f"另外 {impact(r)}")
    head = '沒處理完：' if bad or unk else '都處理完了：'
    text = head + '；'.join(parts) + ('；' if parts else '') + '退款有沒有真的退，目前看不到。'
    first = (bad or unk or [None])[0]
    nxt = f"交給{NEXT_STEP[first['status']][1]}：{NEXT_STEP[first['status']][0]}" if first else '不用處理'
    return text, nxt


AI_CARDS = json.loads((Path(__file__).resolve().parent/'ai-cards.json').read_text(encoding='utf-8')) if (Path(__file__).resolve().parent/'ai-cards.json').exists() else None

QUEUE_WAIT_AVG_MS = {'d24-normal': 323.1229/9, 'd24-slow': 10068.3462/9}
RUNS = [
    # run label, scenario, data source, folder, manifest-file?, metrics file
    ('sep-missing', '漏送通知', 'replay-2026-09', EX/'order-cancel-lifecycle/evidence/runs/missing-notification-20260921-193704', 'metrics.txt'),
    ('sep-fixed', '修好後重跑', 'replay-2026-09', EX/'order-cancel-lifecycle/evidence/runs/missing-notification-20260921-193835', 'metrics.txt'),
    ('sep-slow', '回得慢・資料未齊', 'replay-2026-09', EX/'order-cancel-lifecycle/evidence/runs/slow-sync-control-20260923-191636', 'metrics.txt'),
    ('d24-normal', '正常', 'day24-2026-10-07', D24/'after-normal', 'metrics.prom'),
    ('d24-slow', '回得慢・已收齊', 'day24-2026-10-07', D24/'after-slow', 'metrics.prom'),
]


def metric(text, *names):
    for n in names:
        m = re.search(r'^' + n + r'\s+([\d.]+)', text, re.M)
        if m: return float(m[1])
    return None


def compute():
    rows = []
    for label, scenario, source, folder, mfile in RUNS:
        logs = build.jsonl(folder/'logs.jsonl'); receipts = build.jsonl(folder/'receipts.jsonl')
        mtext = (folder/mfile).read_text(encoding='utf-8-sig')
        depth = metric(mtext, 'oc_notify_queue_depth', 'oc_notification_queue_depth', 'oc_queue_depth')
        if (folder/'manifest.json').exists():
            manifest = build.read_json(folder/'manifest.json')
            if depth is None: depth = manifest.get('last_queue_depth')
        else:
            # Day 24 runs: verify.py confirmed the run finished; the queue snapshot is the end condition.
            result = json.loads((folder/'result.json').read_text(encoding='utf-8-sig'))
            manifest = {'wait': {'terminal': 'day24 verify.py: run finished and queue_depth == 0'}} if depth == 0 else {'wait': {}}
            manifest['day24_result'] = {k: result.get(k) for k in ('cancelled', 'received', 'duplicates') if k in result}
        r = build.reconcile(logs, receipts, manifest, depth)
        if (folder/'manifest.json').exists():
            end_time = ts(build.read_json(folder/'manifest.json').get('ended'))
        else:
            end_time = ts(json.loads((folder/'result.json').read_text(encoding='utf-8-sig')).get('end'))
        r = enrich(r, logs, end_time)
        r['requests_total'], r['outcomes'], r['refund_requested_n'] = request_outcomes(folder)
        r['data_time'] = end_time.astimezone().strftime('%m/%d %H:%M') + ('（重放）' if source.startswith('replay') else '') if end_time else '未知'
        r['_folder'] = folder
        rows.append({'run': label, 'scenario': scenario, 'data_source': source, 'sender_reported_sent': metric(mtext, 'oc_notify_sent_total'),
                     'transitions': metric(mtext, 'oc_transitions_total'), 'enqueued': metric(mtext, 'oc_notify_enqueued_total'), **r})
    return rows


LAST_STEP = {'notify_deferred': '延後', 'notify_enqueued': '排進待送', 'notify_worker_start': '處理中', 'notify_sent': '系統說已送',
             'notify_dead_letter': '放棄', 'notify_failed': '送出失敗'}


def ts(s):
    from datetime import datetime
    return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def enrich(r, logs, end_time):
    """Per-event facts that are already in the raw logs: refund flag, last notify step, cancel time, wait until observation end."""
    cancel = {(x.get('request_id'), x.get('order_id')): x for x in logs if x.get('event') == 'cancel' and x.get('transitioned') is True}
    steps = {}
    for x in logs:
        if str(x.get('event', '')).startswith('notify') and x.get('notification_id'):
            steps[x['notification_id']] = x['event']
    for e in r['events']:
        c = cancel.get((e['request_id'], e['order_id']), {})
        e['refund'] = '退款' if c.get('refund_requested') else '一般'
        e['last_step'] = LAST_STEP.get(steps.get(e['notification_id']), '沒有送出紀錄')
        ct = ts(c.get('ts'))
        e['cancel_time'] = ct.astimezone().strftime('%m/%d %H:%M:%S') if ct else '未知'
        e['waited'] = f"觀察結束時已等 {int((end_time - ct).total_seconds())} 秒" if ct and end_time else '未知'
    bad = [e for e in r['events'] if e['state'] != 'matched']
    r['refund_unmatched'] = sum(e['refund'] == '退款' for e in bad) if r['status'] == 'investigate' else None
    if r['status'] == 'investigate':
        from collections import Counter
        step, n = Counter(e['last_step'] for e in bad).most_common(1)[0]
        r['stuck_detail'] = f"{n} 筆停在「{step}」，之後沒有再送"
    elif r['status'] == 'unknown':
        r['stuck_detail'] = '沒有通知編號，也沒有結束紀錄'
    else:
        r['stuck_detail'] = '—'
    return r


def request_outcomes(folder):
    """Classify every cancel request: success / rejected by rule / duplicate / invalid / system error. Also count refund requests."""
    from collections import Counter
    rows = []
    if (folder/'requests.jsonl').exists():
        for s in (folder/'requests.jsonl').read_text(encoding='utf-8-sig').splitlines():
            if not s.strip(): continue
            x = json.loads(s); body = json.loads(x['response']) if x.get('response') else {}
            rows.append((x.get('http_status'), body))
    else:
        for body in json.loads((folder/'requests.json').read_text(encoding='utf-8-sig')):
            rows.append((200 if body.get('ok') is not None else None, body))
        result = json.loads((folder/'result.json').read_text(encoding='utf-8-sig'))
        if 'repeat_cancel_transitioned' in result:  # Day 24 stores the repeat-cancel check in result.json, not requests.json
            rows.append((200, {'transitioned': result['repeat_cancel_transitioned'], 'ok': True}))
    c = Counter(); refund = 0
    for status, b in rows:
        if status is None or status >= 500: c['系統錯誤'] += 1
        elif b.get('transitioned') is True:
            c['取消成功'] += 1; refund += bool(b.get('refund_requested'))
        elif b.get('reason') == 'rejected_shipped': c['被拒（已出貨）'] += 1
        elif status in (401, 403, 404): c['無效請求'] += 1
        else: c['重複取消'] += 1
    return len(rows), c, refund


STAGE_NOTE = {'6': ('待處理清單', '服務沒有記錄送不出去的通知'), '7': ('退款完成', '沒有接付款系統，看不到錢退了沒')}


def attrs(d): return [{'key': k, 'value': {'stringValue': str(v)}} for k, v in d.items()]


def post(path, body):
    req = urllib.request.Request(OTLP + path, json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r: return r.status


def send(rows, with_logs=True):
    now = str(time.time_ns())
    res = {'attributes': attrs({'service.name': 'day25-work-view', 'deployment.environment': 'local-teaching'})}
    metrics = []
    def gauge(name, desc, value, extra):
        if value is None: return
        metrics.append({'name': name, 'description': desc, 'gauge': {'dataPoints': [{'asDouble': float(value), 'timeUnixNano': now, 'attributes': attrs(extra)}]}})
    for r in rows:
        base = {'run': r['run'], 'scenario': r['scenario'], 'data_source': r['data_source']}
        gauge('work_expected', '應完成的通知數（transitioned=true 的取消）', r['expected'], base)
        gauge('work_matched', '接收端收據且通知 ID 與發送端一致的筆數', r['received'], base)
        gauge('work_unmatched', '應完成但尚未對上的筆數', r['unmatched'], base)
        gauge('work_status', '本輪狀態，值固定為 1，狀態在 status 標籤', 1, {**base, 'status': r['status'], 'reason': r['reason'], 'reason_text': REASON_TEXT.get(r['reason'], r['reason']), 'next_step': NEXT_STEP[r['status']][0], 'owner': NEXT_STEP[r['status']][1], 'status_text': STATUS_TEXT[r['status']], 'stuck_detail': r['stuck_detail'], 'data_time': r['data_time'], 'impact': impact(r)})
        gauge('work_refund_unmatched', '尚未對上的退款通知筆數', r['refund_unmatched'], base)
        gauge('sender_reported_sent', '發送端自報的送出數（oc_notify_sent_total），不是接收端證據', r['sender_reported_sent'], base)
    for r in rows:
        base = {'run': r['run'], 'scenario': r['scenario'], 'data_source': r['data_source']}
        for order, stage, v in [('1', '取消成功', r['transitions']), ('2', '排進待送', r['enqueued']), ('3', '系統說已送', r['sender_reported_sent']), ('4', '對方收到', r['received'])]:
            gauge('work_stage_count', '流程各段的筆數（3 是系統自己回報，4 是對方收據逐筆核對）', v, {**base, 'stage': stage, 'stage_order': order})
        flow = [('1', '收到請求', r['requests_total']), ('2', '取消成功', r['outcomes'].get('取消成功', 0)), ('3', '提出退款', r['refund_requested_n']),
                ('4', '排進待送', r['enqueued']), ('5', '對方收到', r['received'])]
        for order, stage, v in flow:
            gauge('flow_count', '取消流程各段的筆數（1–5 段有資料；系統自報已送不列入流程）', v, {**base, 'stage': stage, 'stage_order': order})
            gauge('flow_stage_info', '流程各段是否有資料', 1, {**base, 'stage': stage, 'stage_order': order, 'available': '有', 'note': '—'})
        for order, (stage, note) in STAGE_NOTE.items():
            gauge('flow_stage_info', '流程各段是否有資料', 1, {**base, 'stage': stage, 'stage_order': order, 'available': '看不到', 'note': note})
        for outcome in ['取消成功', '被拒（已出貨）', '重複取消', '無效請求', '系統錯誤']:
            gauge('request_outcome', '取消請求的結果；被拒、重複取消是業務規則的正常結果', r['outcomes'].get(outcome, 0), {**base, 'outcome': outcome})
        if r['run'] in QUEUE_WAIT_AVG_MS:
            gauge('stage_queue_wait_avg_ms', '平均排隊時間（毫秒），取自 Day 24 Prometheus notification_queue_wait_milliseconds sum/count', QUEUE_WAIT_AVG_MS[r['run']], base)
    s_text, s_next = summary(rows)
    gauge('work_summary', '一句話狀態（固定規則依對帳結果產生）', 1, {'summary': s_text, 'next': s_next})
    if AI_CARDS:
        for run, c in AI_CARDS['cards'].items():
            x = c['card']
            if c['question'] == 'cause':
                key = next((k for k in x['checks'] if 'event' in k['query'] or '延後' in k['result']), x['checks'][0])
                labels = {'question': '可能原因（已用查詢驗證）', 'answer': x['hypothesis'], 'verified': key['result'], 'first_step': x['first_step']}
            else:
                labels = {'question': '缺什麼資料、怎麼補（不推論原因）', 'answer': '\n'.join('• ' + m['what'] for m in x['missing'][:4]),
                          'verified': x['checks'][0]['result'] if x['checks'] else '—', 'first_step': x['first_step']}
            gauge('work_ai_card', 'AI 判斷，待確認：Claude 用唯讀工具查過一輪的調查卡；不影響狀態與負責人', 1,
                  {'run': run, 'scenario': c['scenario'], **labels, 'generated_at': ts(AI_CARDS['generated_at']).astimezone().strftime('%m/%d %H:%M')})
    post('/v1/metrics', {'resourceMetrics': [{'resource': res, 'scopeMetrics': [{'scope': {'name': 'day25-publish'}, 'metrics': metrics}]}]})
    if not with_logs: return len(metrics), 0
    records = []
    for r in rows:
        for e in r['events']:
            if e['state'] == 'matched': continue
            # In a run whose status is unknown, an unmatched event is not evidence of loss.
            st, sev, word = ('unknown_identity', 'INFO', '資料不足，無法判斷') if r['status'] == 'unknown' else (e['state'], 'WARN', '未對上')
            records.append({'timeUnixNano': now, 'severityText': sev, 'body': {'stringValue': f"{r['run']} {word}：order={e['order_id']} notification={e['notification_id']}"},
                            'attributes': attrs({'run': r['run'], 'scenario': r['scenario'], 'data_source': r['data_source'], 'state': st,
                                                 'order_id': e['order_id'], 'request_id': e['request_id'], 'notification_id': e['notification_id'] or 'unknown',
                                                 'refund': e['refund'], 'last_step': e['last_step'], 'cancel_time': e['cancel_time'], 'waited': e['waited']})})
        if r['status'] == 'unknown':
            records.append({'timeUnixNano': now, 'severityText': 'INFO', 'body': {'stringValue': f"{r['run']} 資料不足：{r['reason']}，先補資料"},
                            'attributes': attrs({'run': r['run'], 'scenario': r['scenario'], 'data_source': r['data_source'], 'state': 'unknown', 'reason': r['reason']})})
    post('/v1/logs', {'resourceLogs': [{'resource': res, 'scopeLogs': [{'scope': {'name': 'day25-publish'}, 'logRecords': records}]}]})
    # Raw evidence a real system would have: service logs and receiver receipts, replayed with today's time; original ts kept.
    base_ns = time.time_ns()
    for svc, fname in [('order-api-replay', 'logs.jsonl'), ('notify-receiver-replay', 'receipts.jsonl')]:
        recs = []
        for r in rows:
            f = r['_folder']/fname
            if not f.exists(): continue
            for i, line in enumerate(l for l in f.read_text(encoding='utf-8-sig').splitlines() if l.strip()):
                x = json.loads(line)
                keep = {k: x.get(k) for k in ('event', 'order_id', 'request_id', 'notification_id', 'transitioned', 'refund_requested', 'kind') if x.get(k) is not None}
                recs.append({'timeUnixNano': str(base_ns + len(recs)), 'severityText': 'INFO', 'body': {'stringValue': line},
                             'attributes': attrs({'run': r['run'], 'scenario': r['scenario'], 'data_source': r['data_source'],
                                                  'original_ts': x.get('ts') or x.get('received_at') or '', **keep})})
        rres = {'attributes': attrs({'service.name': svc, 'deployment.environment': 'local-teaching'})}
        for i in range(0, len(recs), 200):
            post('/v1/logs', {'resourceLogs': [{'resource': rres, 'scopeLogs': [{'scope': {'name': 'day25-raw'}, 'logRecords': recs[i:i+200]}]}]})
    return len(metrics), len(records)


def main():
    rows = compute()
    (ROOT/'grafana-publish-rows.json').write_text(json.dumps([{k: (dict(v) if k == 'outcomes' else v) for k, v in r.items() if k != 'events' and not k.startswith('_')} for r in rows], ensure_ascii=False, indent=2), encoding='utf-8')
    loop = int(sys.argv[sys.argv.index('--loop')+1]) if '--loop' in sys.argv else 0
    first = '--no-logs' not in sys.argv  # logs (and raw replay) are sent once; later loops only refresh gauges
    while True:
        m, l = send(rows, with_logs=first)  # logs once; gauges re-sent so Prometheus keeps a fresh sample
        first = False
        print(time.strftime('%H:%M:%S'), 'sent', m, 'metrics', l, 'log records', flush=True)
        if not loop: break
        time.sleep(loop)

if __name__ == '__main__': main()
