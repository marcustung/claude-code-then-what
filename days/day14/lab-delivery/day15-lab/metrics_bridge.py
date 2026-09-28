from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
P=Path(__file__).parent/'current-metrics.prom'
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/plain; version=0.0.4');self.end_headers();self.wfile.write(P.read_bytes() if P.exists() else b'day15_bridge_up 1\n')
 def log_message(self,*a):pass
HTTPServer(('127.0.0.1',19115),H).serve_forever()
