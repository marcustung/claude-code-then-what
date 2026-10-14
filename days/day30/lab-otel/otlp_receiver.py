"""Tiny local OTLP/HTTP-JSON receiver: accepts POST /v1/metrics, /v1/logs, /v1/traces and appends each body to <dir>/<signal>.jsonl.
No Grafana, nothing leaves the machine. Point Claude Code at it with:
  CLAUDE_CODE_ENABLE_TELEMETRY=1  OTEL_METRICS_EXPORTER=otlp  OTEL_LOGS_EXPORTER=otlp
  OTEL_EXPORTER_OTLP_PROTOCOL=http/json  OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
usage: python otlp_receiver.py <dir> [port]"""
import json, sys, threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

DIR = Path(sys.argv[1]); DIR.mkdir(parents=True, exist_ok=True)
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4318
lock = threading.Lock()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(n)
        sig = self.path.rstrip('/').split('/')[-1]               # metrics | logs | traces
        try: payload = json.loads(body or b'{}')
        except Exception: payload = {'non_json_bytes': len(body), 'content_type': self.headers.get('Content-Type')}
        with lock, open(DIR / f'{sig}.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({'received_at': datetime.now(timezone.utc).isoformat(), 'payload': payload}, ensure_ascii=False) + '\n')
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(b'{}')


ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
