# -*- coding: utf-8 -*-
"""實驗 3：從 Day 21 的 complete 案例衍生 6 個較難案例；連同原本 3 個共 9 個。正解（EXPECTED）跑前固定。
迴圈不得修改本檔、cases/、eval.py（LOCK.json）。

  python skill-lab/build_cases.py
"""
from pathlib import Path
import json, shutil

ROOT = Path(__file__).resolve().parent
SRC = Path(r'<REPO>\examples\day21-skill-eval\cases')
OUT = ROOT / 'cases'

EXPECTED = {
    'complete':          ('confirmed', 'confirmed', 'Day 21 原案例'),
    'missing-receipts':  ('confirmed', 'unknown', 'Day 21 原案例'),
    'decoy-receipt':     ('confirmed', 'unknown', 'Day 21 原案例'),
    'h1-receipt-500':    ('confirmed', 'unknown', '收據存在但接收端回 500：沒有成功接收的證據'),
    'h2-dead-but-received': ('unknown', 'confirmed', '發送端只有失敗與死信、沒有 notify_sent；接收端有 200 收據'),
    'h3-receipt-before-cancel': ('confirmed', 'unknown', '收據時間早於取消事件，證據自相矛盾，不能採信'),
    'h4-duplicate-receipts': ('confirmed', 'confirmed', '同一通知收到兩次 200：重複不代表沒送到'),
    'h5-no-sender-log':  ('unknown', 'confirmed', '沒有任何發送紀錄，只有接收端收據'),
    'h6-payload-mismatch': ('confirmed', 'unknown', '收據的 refund_requested 與 log 相反：收到的不是這則通知的正確內容'),
}


def jl(p):
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def wjl(p, rows):
    p.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    for name in ('complete', 'missing-receipts', 'decoy-receipt'):
        shutil.copytree(SRC / name, OUT / name)
    base = OUT / 'complete'
    logs = jl(base / 'data' / 'logs.jsonl')
    rec = json.loads((base / 'data' / 'receipts.json').read_text(encoding='utf-8'))
    nid = next(r['notification_id'] for r in logs if r.get('event') == 'notify_sent')
    cancel_ts = next(r['ts'] for r in logs if r.get('event') == 'cancel')

    def make(name, logs2, rec2):
        d = OUT / name
        shutil.copytree(base, d)
        wjl(d / 'data' / 'logs.jsonl', logs2)
        (d / 'data' / 'receipts.json').write_text(json.dumps(rec2, ensure_ascii=False, indent=2), encoding='utf-8')
        (d / 'CASE.md').write_text(f'# {name}\n\n（案例說明不給受測者看；正解見 build_cases.py EXPECTED）\n', encoding='utf-8')

    r500 = json.loads(json.dumps(rec)); r500[0]['status'] = 500
    make('h1-receipt-500', logs, r500)

    dead = [r for r in logs if r.get('event') != 'notify_sent']
    for a in range(4):
        dead.append({'level': 'WARN', 'event': 'notify_attempt_failed', 'notification_id': nid, 'attempt': a, 'error': 'HttpRequestException', 'ts': cancel_ts})
    dead.append({'level': 'ERROR', 'event': 'notify_dead_letter', 'notification_id': nid, 'order_id': rec[0]['payload']['order_id'], 'attempts': 4, 'ts': cancel_ts})
    make('h2-dead-but-received', dead, rec)

    early = json.loads(json.dumps(rec)); early[0]['at'] = early[0]['at'] - 3600
    make('h3-receipt-before-cancel', logs, early)

    make('h4-duplicate-receipts', logs, rec + json.loads(json.dumps(rec)))

    make('h5-no-sender-log', [r for r in logs if r.get('event') != 'notify_sent'], rec)

    mism = json.loads(json.dumps(rec)); mism[0]['payload']['refund_requested'] = not mism[0]['payload'].get('refund_requested', False)
    make('h6-payload-mismatch', logs, mism)

    (ROOT / 'expected.json').write_text(json.dumps({k: {'sender_status': v[0], 'receiver_status': v[1], 'why': v[2]} for k, v in EXPECTED.items()},
                                                   ensure_ascii=False, indent=2), encoding='utf-8')
    print('cases:', sorted(p.name for p in OUT.iterdir()))


if __name__ == '__main__':
    main()
