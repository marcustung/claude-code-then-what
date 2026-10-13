"""Day 20 v2：整理本包 JSON 成來源清單。v1 欄位不變，另加 records 給 check_result.py 讀。

不查遠端、不判根因。receipts.json 沒有版本欄位，接收紀錄的 version 沿用同一通知 ID 的
notify_sent，並以 version_source 標明；找不到對應發送紀錄就留空，不自行補。
"""
from pathlib import Path
import json, sys


def collect(root):
    root = Path(root)
    task = json.loads((root / 'task.json').read_text(encoding='utf-8-sig'))
    order = task['order_id']
    out = {'order_id': order, 'expected_version': task['version'], 'sources': {}, 'missing_sources': [],
           'errors': [], 'events': [], 'receipts': [], 'records': []}
    sent_version = {}
    for name in ['logs.jsonl', 'receipts.json']:
        p = root / 'data' / name
        if not p.exists():
            out['sources'][name] = 'missing'; out['missing_sources'].append(name); continue
        try:
            raw = p.read_text(encoding='utf-8-sig')
            rows = [json.loads(x) for x in raw.splitlines() if x.strip()] if name.endswith('jsonl') else json.loads(raw)
            if not isinstance(rows, list) or any(not isinstance(x, dict) for x in rows):
                raise ValueError('expected object records')
            out['sources'][name] = 'present'
            if name == 'logs.jsonl':
                ids = {x.get('notification_id') for x in rows if x.get('order_id') == order and x.get('notification_id')}
                for n, x in enumerate(rows, 1):
                    if x.get('order_id') == order or x.get('notification_id') in ids:
                        out['events'].append({'source': f'data/{name}:{n}', 'record': x})
                    if x.get('event') == 'notify_sent' and x.get('order_id') == order:
                        sent_version[x.get('notification_id')] = x.get('version')
                        out['records'].append({'ref': f'log:{n}', 'side': 'sender', 'event': 'notify_sent',
                                               'order_id': order, 'notification_id': x.get('notification_id'),
                                               'version': x.get('version'), 'source': f'data/{name}:{n}'})
            else:
                for n, x in enumerate(rows):
                    pl = x.get('payload', {})
                    if pl.get('order_id') == order:
                        out['receipts'].append({'source': f'data/{name} item {n}', 'record': x})
                        nid = pl.get('notification_id')
                        out['records'].append({'ref': f'receipt:{n}', 'side': 'receiver', 'event': 'notification_received',
                                               'order_id': order, 'notification_id': nid,
                                               'version': sent_version.get(nid),
                                               'version_source': 'inherited-from-notify_sent' if nid in sent_version else 'none',
                                               'source': f'data/{name} item {n}'})
        except (ValueError, TypeError) as e:
            out['sources'][name] = 'invalid'; out['errors'].append({'source': name, 'error': str(e)})
    out['notification_ids'] = sorted({r['notification_id'] for r in out['records'] if r['side'] == 'sender' and r['notification_id']})
    return out


if __name__ == '__main__':
    root = Path(sys.argv[1])
    result = collect(root)
    (root / 'evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'sources': result['sources'], 'records': len(result['records']),
                      'notification_ids': result['notification_ids']}, ensure_ascii=False))
    sys.exit(2 if result['errors'] else 0)
