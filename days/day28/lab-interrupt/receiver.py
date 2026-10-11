"""Loopback teaching receiver for the interrupt experiment.
POST /send {op_id, event_id}: dedupes by op_id only (the contract under test); every non-duplicate is an effect.
GET /receipt?event_id=E1: what the receiver knows about that event (delivered / not_found).
usage: python receiver.py <port> <effects.jsonl>"""
import json, sys, threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT, LOG = int(sys.argv[1]), sys.argv[2]
lock = threading.Lock(); seen = {}; effects = []


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def reply(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(code)
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/health': return self.reply(200, {'ok': True})
        if u.path == '/receipt':
            eid = parse_qs(u.query).get('event_id', [''])[0]
            with lock: hit = [e for e in effects if e['event_id'] == eid]
            return self.reply(200, {'event_id': eid, 'status': 'delivered' if hit else 'not_found',
                                    'first_delivered_at': hit[0]['at'] if hit else None})
        self.reply(404, {'error': 'not_found'})

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = json.loads(self.rfile.read(n) or b'{}')
        op, eid = body.get('op_id'), body.get('event_id')
        with lock:
            if op in seen: return self.reply(200, {'duplicate': True, **seen[op]})
            e = {'at': datetime.now(timezone.utc).isoformat(), 'op_id': op, 'event_id': eid, 'notice_no': len(effects) + 1}
            effects.append(e); seen[op] = {'event_id': eid, 'notice_no': e['notice_no']}
            with open(LOG, 'a', encoding='utf-8') as f: f.write(json.dumps(e) + '\n')
        self.reply(200, {'accepted': True, 'event_id': eid, 'notice_no': e['notice_no']})


ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
