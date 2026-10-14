"""Loopback teaching service: notification source + work-item tracker.
GET  /notifications          today's notification status (or 503 when --source-down)
POST /items {order, kind}    open a work item; mode 'new' always creates, 'dedupe' keys on order+kind
Every request is appended to <dir>/requests.jsonl; items are kept in <dir>/items.json.
usage: python service.py <port> <dir> <new|dedupe> [--dup-row] [--source-down] [--keep] [--today]
  --keep   keep items.json across restarts (nightly use)
  --today  stamp notifications with today's date instead of the fixed 2026-10-11 (nightly use)"""
import json, sys, threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT, DIR, MODE = int(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
DUP_ROW, DOWN = '--dup-row' in sys.argv, '--source-down' in sys.argv
KEEP, TODAY = '--keep' in sys.argv, '--today' in sys.argv
lock = threading.Lock(); items = []
ROWS = [
    {'id': 'N1', 'order': 'O-1001', 'status': 'delivered', 'at': '2026-10-11T01:02:11Z'},
    {'id': 'N2', 'order': 'O-1002', 'status': 'timeout', 'at': '2026-10-11T01:05:40Z'},
    {'id': 'N3', 'order': 'O-1003', 'status': 'delivered', 'at': '2026-10-11T01:07:03Z'},
    {'id': 'N4', 'order': 'O-1004', 'status': 'bounced', 'at': '2026-10-11T01:09:27Z'},
    {'id': 'N5', 'order': 'O-1005', 'status': 'delivered', 'at': '2026-10-11T01:12:55Z'},
]
DAY = datetime.now().strftime('%Y-%m-%d') if TODAY else '2026-10-11'
if TODAY:
    ROWS = [{**r, 'at': DAY + r['at'][10:]} for r in ROWS]
if DUP_ROW:
    ROWS.append({'id': 'N6', 'order': 'O-1002', 'status': 'timeout', 'at': '2026-10-11T01:31:08Z'})


def now(): return datetime.now(timezone.utc).isoformat()


def log(rec):
    with open(DIR / 'requests.jsonl', 'a', encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False) + '\n')


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def reply(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(code)
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        run = self.headers.get('X-Run', '')
        if self.path == '/health': return self.reply(200, {'ok': True})
        if self.path == '/notifications':
            code = 503 if DOWN else 200
            with lock: log({'at': now(), 'run': run, 'req': 'GET /notifications', 'code': code})
            if DOWN: return self.reply(503, {'error': 'source_unavailable'})
            return self.reply(200, {'date': DAY, 'notifications': ROWS})
        self.reply(404, {'error': 'not_found'})

    def do_POST(self):
        run = self.headers.get('X-Run', '')
        n = int(self.headers.get('Content-Length', 0)); body = json.loads(self.rfile.read(n) or b'{}')
        order, kind = body.get('order'), body.get('kind')
        with lock:
            hit = next((i for i in items if i['order'] == order and i['kind'] == kind), None) if MODE == 'dedupe' else None
            if hit:
                hit['count'] += 1; hit['runs'].append(run); res = {'item_id': hit['item_id'], 'existing': True, 'count': hit['count']}
            else:
                it = {'item_id': f'W-{len(items) + 1:03d}', 'order': order, 'kind': kind, 'count': 1, 'opened_at': now(), 'runs': [run]}
                items.append(it); res = {'item_id': it['item_id'], 'existing': False, 'count': 1}
            (DIR / 'items.json').write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
            log({'at': now(), 'run': run, 'req': 'POST /items', 'order': order, 'kind': kind, **res})
        self.reply(200, res)


DIR.mkdir(parents=True, exist_ok=True)
if KEEP and (DIR / 'items.json').exists():
    items.extend(json.loads((DIR / 'items.json').read_text(encoding='utf-8')))
else:
    (DIR / 'items.json').write_text('[]', encoding='utf-8')
ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
