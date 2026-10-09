"""Day 25 investigation card: rules pick the question by status; Claude answers it with Day 24's read-only gcx MCP.
Every query is written to an audit file; the grader checks the card's queries against it. Cards are cached to ai-cards.json."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, os, subprocess, sys, time
import publish_to_grafana as pub

ROOT = Path(__file__).resolve().parent
MCP = ROOT.parent/'day24-observability-lab/gcx_readonly_mcp.py'
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
VIEWER_CFG = os.path.join(os.environ['TEMP'], 'day24-gcx-private.yaml')

Q_CAUSE = ('問題：這一項的可能原因是什麼？請先提出假設，再用查詢工具實際驗證（至少一次），最後說值班的人先查哪裡。'
           '用「可能」「疑似」，不要說成確定；卡片上的每個查詢都必須是你真的執行過的。')
Q_MISSING = ('問題：這一項的紀錄不全，現在判斷不了。請回答：缺了哪些資料？為什麼需要它？要怎麼補？'
             '不要推論原因（不要寫「可能沒送出」「對方故障」這類判斷）。可以用查詢工具確認哪些資料確實缺了。')
# The card is shown to on-call people on the dashboard, so every field except `query` uses the dashboard's plain words.
PLAIN = ('寫法：卡片會直接顯示在 Dashboard 給值班的人看。除了 query 欄，所有欄位都用白話：不要出現英文單字、事件名、欄位名、指標名、檔名、'
         '契約條號、工具名，改用下面的詞；每個欄位 60 字以內，只寫結論，不寫查詢過程。訂單編號（例如 o-01）可以照寫。'
         '查詢沒有結果時，只能寫「沒查到」並說明，不能寫成「沒有這些紀錄」。'
         'query 欄照實寫你真的執行過的查詢（給稽核比對用，不會顯示）。\n'
         '對照：notify_deferred→延後；notify_enqueued、enqueue、待送佇列→排進待送；queue_depth→待送數量；notify_sent→系統記錄已送；'
         'notify_failed、failed→送出失敗；retry→重送；dead_letter→待處理清單（送不出去要進的清單）；receipts、收據、接收端→對方收據、對方收到；'
         'notification_id→通知編號；order_id→訂單編號；request_id→請求編號；cancel→取消紀錄；startup→服務啟動紀錄；終態→結束紀錄（每筆通知最後的結果）；'
         'logs、logs.jsonl、Log→服務紀錄；metrics、/metrics、指標→系統統計數字；run、sep-missing、sep-slow→用項目名稱（例如「這一次」「漏送通知那次」）；'
         'NC-05 這類條號→直接說規定內容；Loki、Prometheus、Grafana→不寫工具名。')
SCHEMA_CAUSE = {'type': 'object', 'additionalProperties': False, 'required': ['hypothesis', 'checks', 'conclusion', 'cannot_see', 'first_step'],
    'properties': {'hypothesis': {'type': 'string'}, 'conclusion': {'type': 'string'}, 'first_step': {'type': 'string'},
                   'cannot_see': {'type': 'array', 'items': {'type': 'string'}},
                   'checks': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['why', 'query', 'result'],
                              'properties': {'why': {'type': 'string'}, 'query': {'type': 'string'}, 'result': {'type': 'string'}}}}}}
SCHEMA_MISSING = {'type': 'object', 'additionalProperties': False, 'required': ['missing', 'checks', 'first_step'],
    'properties': {'first_step': {'type': 'string'},
                   'missing': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['what', 'why_needed', 'how_to_add'],
                               'properties': {'what': {'type': 'string'}, 'why_needed': {'type': 'string'}, 'how_to_add': {'type': 'string'}}}},
                   'checks': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['why', 'query', 'result'],
                              'properties': {'why': {'type': 'string'}, 'query': {'type': 'string'}, 'result': {'type': 'string'}}}}}}


def main():
    # --window-minutes keeps queries on the latest replay only (each publisher start re-sends the raw logs).
    minutes = int(sys.argv[sys.argv.index('--window-minutes')+1]) if '--window-minutes' in sys.argv else 30
    tag = '-' + sys.argv[sys.argv.index('--tag')+1] if '--tag' in sys.argv else ''
    run_dir = ROOT/'runs-ai-card'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + tag); run_dir.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    window = {'start': (now - timedelta(minutes=minutes)).strftime('%Y-%m-%dT%H:%M:%SZ'), 'end': (now + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ')}
    out = {'generated_at': now.isoformat(), 'model': 'sonnet', 'cards': {}}
    for r in pub.compute():
        if r['status'] not in ('investigate', 'unknown'): continue
        kind = 'cause' if r['status'] == 'investigate' else 'missing'
        bad = [e for e in r['events'] if e['state'] != 'matched']
        ctx = {'項目': r['scenario'], 'run 標籤': r['run'], '狀態（規則判定）': pub.STATUS_TEXT[r['status']], '資料時間': r['data_time'],
               '卡在哪（規則判定）': r['stuck_detail'], '影響': pub.impact(r),
               '流程各段筆數': {'收到請求': r['requests_total'], '取消成功': r['outcomes'].get('取消成功', 0), '排進待送': r['enqueued'], '對方收到': r['received']},
               '系統自己記錄的已送出數（不是送達證據）': r['sender_reported_sent'],
               '沒對上的通知編號（前 10 筆）': [e['notification_id'] for e in bad if e['notification_id']][:10]}
        prompt = ('你是協助值班人員的助手。這是本機教學用的 Grafana，資料是重放的教學紀錄。Dashboard 上這一項亮了燈，規則已經決定狀態、數字和負責人。\n\n'
                  + (Q_CAUSE if kind == 'cause' else Q_MISSING) +
                  '\n\n可用的查詢工具 query_observability（唯讀）。Loki 裡有三種資料（service_name）：day25-work-view（對帳結果）、order-api-replay（服務原始 Log，'
                  '每筆帶 run、event、order_id、request_id、notification_id、original_ts）、notify-receiver-replay（對方收據）。Prometheus 的 job="day25-work-view" 有對帳指標。'
                  f'查 Log 時 start 用 {window["start"]}、end 用 {window["end"]}。'
                  'run 是每筆紀錄上的欄位，不是串流標籤，要用 {service_name="…"} | run="…" 篩選這一項。\n\n'
                  '這一項的 Dashboard 資訊：\n' + json.dumps(ctx, ensure_ascii=False, indent=2) + '\n\n通知契約：\n' + SPEC.read_text(encoding='utf-8') +
                  '\n\n全部用繁體中文。' + PLAIN)
        w = run_dir/r['run']; w.mkdir()
        audit = w/'tool-audit.jsonl'
        cfg = {'mcpServers': {'observability': {'command': 'python', 'args': [str(MCP)],
               'env': {'GCX_CONFIG': VIEWER_CFG, 'DAY24_TOOL_AUDIT': str(audit), 'PYTHONUTF8': '1'}}}}
        (w/'mcp.json').write_text(json.dumps(cfg), encoding='utf-8'); (w/'prompt.txt').write_text(prompt, encoding='utf-8')
        args = ['claude', '-p', '--model', 'sonnet', '--restricted', '--tools', '', '--allowedTools', 'mcp__observability__query_observability',
                '--strict-mcp-config', '--mcp-config', str(w/'mcp.json'), '--setting-sources', 'project',
                '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}), '--no-session-persistence',
                '--output-format', 'json', '--json-schema', json.dumps(SCHEMA_CAUSE if kind == 'cause' else SCHEMA_MISSING), '--max-budget-usd', '1.5']
        t0 = time.time()
        p = subprocess.run(args, input=prompt, cwd=w, capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONUTF8': '1'}, timeout=900)
        (w/'stdout.json').write_text(p.stdout, encoding='utf-8'); (w/'stderr.txt').write_text(p.stderr, encoding='utf-8')
        res = json.loads(p.stdout)
        card = res.get('structured_output') or json.loads(res.get('result') or '{}')
        out['cards'][r['run']] = {'scenario': r['scenario'], 'question': kind, 'card': card, 'cost_usd': res.get('total_cost_usd'),
                                  'elapsed_seconds': round(time.time()-t0, 1), 'audit': str(audit.relative_to(ROOT))}
        print(r['run'], kind, json.dumps(card, ensure_ascii=False)[:1500])
    (ROOT/'ai-cards.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    (run_dir/'ai-cards.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(run_dir)

if __name__ == '__main__': main()
