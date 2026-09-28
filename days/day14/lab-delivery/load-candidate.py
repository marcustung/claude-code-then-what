"""Run k6 against an existing package; compare successful notifications after draining."""
from pathlib import Path
import argparse,collections,hashlib,http.server,json,os,socket,subprocess,threading,time,urllib.request
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('--candidate',default='candidate-checked');ap.add_argument('--k6',required=True);a=ap.parse_args()
for value in [a.name,a.candidate]:
 if not value.replace('-','').replace('_','').isalnum():ap.error('simple run name required')
run=ROOT/'runs'/a.name;run.mkdir(exist_ok=False);package=ROOT/'runs'/a.candidate/'package'
def digest():return {str(p.relative_to(package)).replace(chr(92),'/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in package.rglob('*') if p.is_file()}
before=digest();expected={k.replace(chr(92),'/'):v for k,v in json.loads((package.parent/'package-manifest.json').read_text()).items()}
if before!=expected:raise RuntimeError('package changed')
receipts=[];samples=[];lock=threading.Lock();stop=threading.Event();proc=None
class Sink(http.server.BaseHTTPRequestHandler):
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  with lock:receipts.append(dict(at=time.time(),payload=body))
  self.send_response(200);self.end_headers();self.wfile.write(b'{}')
 def log_message(self,*args):pass
sink=http.server.ThreadingHTTPServer(('127.0.0.1',0),Sink);threading.Thread(target=sink.serve_forever,daemon=True).start()
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
base=f'http://127.0.0.1:{port}'
def get(path):
 with urllib.request.urlopen(base+path,timeout=3) as res:return res.read().decode()
def sample():
 while not stop.wait(.5):
  try:samples.append(dict(at=time.time(),metrics=get('/metrics')))
  except Exception as e:samples.append(dict(at=time.time(),error=type(e).__name__))
report={'passed':False,'candidate':a.candidate,'before_sha256':before,'scope':'loopback single process, synthetic 250ms threshold, not production capacity or SLA'}
out=(run/'stdout.txt').open('w');err=(run/'stderr.txt').open('w');sampler=None
try:
 env=os.environ.copy()
 for k in ['OC_FAULTS','OC_TEST_DELAY_MS']:env.pop(k,None)
 env.update(ASPNETCORE_URLS=base,OC_RUN_DIR=str(run),OC_SINK_URL=f'http://127.0.0.1:{sink.server_port}/notify')
 proc=subprocess.Popen(['dotnet',str(package/'Api.dll')],env=env,cwd=package,stdout=out,stderr=err)
 deadline=time.monotonic()+20
 while True:
  try:report['health']=json.loads(get('/health'));break
  except OSError:
   if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('startup failed')
   time.sleep(.1)
 sampler=threading.Thread(target=sample,daemon=True);sampler.start()
 e=env.copy();e.update(BASE_URL=base,RUN_ID=a.name)
 c=subprocess.run([a.k6,'run','--summary-export',str(run/'k6-summary.json'),'--out','json='+str(run/'k6-samples.json'),str(ROOT/'load-candidate.js')],env=e,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
 (run/'k6-console.txt').write_text(c.stdout+c.stderr,encoding='utf-8');report['k6_exit']=c.returncode
 deadline=time.monotonic()+20
 while True:
  logs=[json.loads(x) for x in (run/'logs.jsonl').read_text(encoding='utf-8').splitlines()]
  transitions=[x for x in logs if x.get('event')=='cancel' and x.get('transitioned')]
  sent=[x for x in logs if x.get('event')=='notify_sent']
  if len(sent)>=len(transitions) or time.monotonic()>deadline:break
  time.sleep(.1)
 time.sleep(.3)
 ns=collections.Counter(x.get('notification_id') for x in transitions)
 received=collections.Counter(x['payload']['notification_id'] for x in receipts)
 sentids=collections.Counter(x['notification_id'] for x in sent)
 checks={'manifest_unchanged':digest()==before,'load_passed':c.returncode==0,'has_transitions':len(transitions)>0,'one_transition_per_order':len({x['order_id'] for x in transitions})==len(transitions),'notification_identity_complete':None not in ns,'receipts_match_transitions_once':ns==received and all(v==1 for v in received.values()),'sent_matches_receipts':sentids==received}
 report.update(checks=checks,passed=all(checks.values()),transitions=len(transitions),receipts=len(receipts),sent=len(sent),after_sha256=digest())
except Exception as e:report['error']=repr(e)
finally:
 stop.set()
 if sampler:sampler.join(timeout=5)
 if proc:
  proc.terminate()
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
 sink.shutdown();sink.server_close();out.close();err.close()
 for name,data in [('report.json',report),('receipts.json',receipts),('metrics-samples.json',samples)]:
  (run/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['passed'] else 1)
