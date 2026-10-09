"""Generate the 'AI 判斷' demo field: one claude -p call per problem item, evidence only, cached to ai-hints.json.
Rules and code still own status, numbers and owner; this field is labelled as an unconfirmed AI judgement."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, subprocess, os
import publish_to_grafana as pub

ROOT = Path(__file__).resolve().parent
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
SCHEMA = json.dumps({'type': 'object', 'additionalProperties': False,
    'required': ['likely_cause', 'evidence', 'first_check', 'confidence', 'cannot_see'],
    'properties': {'likely_cause': {'type': 'string'}, 'evidence': {'type': 'array', 'items': {'type': 'string'}},
                   'first_check': {'type': 'string'}, 'confidence': {'type': 'string', 'enum': ['高', '中', '低', '無法判斷']},
                   'cannot_see': {'type': 'array', 'items': {'type': 'string'}}}})


def evidence(r):
    bad = [e for e in r['events'] if e['state'] != 'matched']
    return {'項目': r['scenario'], '狀態': pub.STATUS_TEXT[r['status']], '資料時間': r['data_time'],
            '流程各段筆數': {'收到請求': r['requests_total'], '取消成功': r['outcomes'].get('取消成功', 0), '提出退款': r['refund_requested_n'],
                         '排進待送': r['enqueued'], '對方收到（收據逐筆核對）': r['received']},
            '請求結果': dict(r['outcomes']),
            '系統自己記錄的已送出數（不是送達證據）': r['sender_reported_sent'],
            '沒對上的通知：最後停在哪一步': dict(Counter(e['last_step'] for e in bad)),
            '沒對上的通知：其中退款通知': sum(e['refund'] == '退款' for e in bad),
            '沒對上的通知：有通知編號的筆數': sum(bool(e['notification_id']) for e in bad),
            '看不到的段落': {'待處理清單（送不出去要進清單）': '服務沒有這個紀錄', '退款完成': '沒有監控，不接付款服務'},
            '這一項的結束紀錄': '有' if r.get('observation_closed') else '沒有'}


def main():
    out = {'generated_at': datetime.now(timezone.utc).isoformat(), 'model': 'sonnet', 'hints': {}}
    spec = SPEC.read_text(encoding='utf-8')
    for r in pub.compute():
        if r['status'] not in ('investigate', 'unknown'): continue
        ev = evidence(r)
        prompt = ('你是協助值班人員的助手。下面是 Dashboard 背後的證據（JSON）與通知契約。'
                  '請判斷「這一項為什麼可能會這樣、值班的人應該先查哪裡」。規則：只能根據給你的證據推論；'
                  '用「可能」「疑似」，不要說成確定；每個推論都要附依據；看不到的就說看不到，不要猜；'
                  '狀態、數字、負責人已由規則決定，你不用重複。全部用繁體中文，每個欄位一句話。\n\n'
                  '證據：\n' + json.dumps(ev, ensure_ascii=False, indent=2) + '\n\n通知契約：\n' + spec)
        p = subprocess.run(['claude', '-p', '--model', 'sonnet', '--tools', '', '--setting-sources', '', '--no-session-persistence',
                            '--output-format', 'json', '--json-schema', SCHEMA], input=prompt, capture_output=True, text=True,
                           encoding='utf-8', env={**os.environ, 'PYTHONUTF8': '1'}, timeout=600)
        res = json.loads(p.stdout)
        hint = res.get('structured_output') or json.loads(res.get('result', '{}'))
        out['hints'][r['run']] = {'scenario': r['scenario'], 'hint': hint, 'evidence': ev,
                                  'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'cost_usd': res.get('total_cost_usd')}
        print(r['run'], json.dumps(hint, ensure_ascii=False))
    (ROOT/'ai-hints.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__': main()
