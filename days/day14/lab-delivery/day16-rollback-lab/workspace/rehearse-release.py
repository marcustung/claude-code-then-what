"""Local update/rollback rehearsal. Never deploys externally or replays failed notifications."""
from pathlib import Path
import argparse,hashlib,http.server,json,os,socket,subprocess,threading,time,urllib.request,urllib.error
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('--old',default='candidate-checked');ap.add_argument('--new',default='acceptance-next-01');a=ap.parse_args()
for name in [a.name,a.old,a.new]:
 if not name.replace('-','').replace('_','').isalnum():ap.error('simple name required')
o=R/'runs'/a.name;o.mkdir(exist_ok=False)
checks=[];events=[];receipts=[];proc=None;streams=[];phase='';sink_status=200

def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def check(name,value,detail):checks.append(dict(name=name,passed=bool(value),detail=detail))
def manifest(p):return {str(x.relative_to(p)).replace(chr(92),'/'):hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file()}
class Sink(http.server.BaseHTTPRequestHandler):
 def do_POST(self):
  payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  receipts.append(dict(at=time.time(),phase=phase,status=sink_status,payload=payload))
  self.send_response(sink_status);self.end_headers();self.wfile.write(b'{}')
 def log_message(self,*args):pass
sink=http.server.ThreadingHTTPServer(('127.0.0.1',0),Sink);threading.Thread(target=sink.serve_forever,daemon=True).start()
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
base=f'http://127.0.0.1:{port}'
def request(method,path,body=None):
 req=urllib.request.Request(base+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-Actor':'rehearsal-author','X-Request-Id':phase+'-request','X-Run-Id':a.name})
 try:
  with urllib.request.urlopen(req,timeout=5) as v:status=v.status;text=v.read().decode()
 except urllib.error.HTTPError as e:status=e.code;text=e.read().decode()
 try:data=json.loads(text)
 except ValueError:data=text
 events.append(dict(at=time.time(),phase=phase,method=method,path=path,status=status,response=data))
 return status,data
def stop():
 global proc
 if proc:
  proc.terminate()
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
  proc=None
 for f in streams:f.close()
 streams.clear()
def start(which,label,status):
 global proc,phase,sink_status
 stop();phase=label;sink_status=status;p=R/'runs'/which/'package';d=o/label;d.mkdir()
 expected={k.replace(chr(92),'/'):v for k,v in json.loads((p.parent/'package-manifest.json').read_text()).items()}
 check(label+'-package',manifest(p)==expected,which)
 if manifest(p)!=expected:raise RuntimeError('package integrity failed')
 if not json.loads((p.parent/'report.json').read_text())['passed']:raise RuntimeError('unverified candidate')
 env=os.environ.copy()
 for key in ['OC_FAULTS','OC_TEST_DELAY_MS']:env.pop(key,None)
 env.update(ASPNETCORE_URLS=base,OC_RUN_DIR=str(d),OC_SINK_URL=f'http://127.0.0.1:{sink.server_port}/notify')
 streams.extend([(d/'stdout.txt').open('w'),(d/'stderr.txt').open('w')])
 proc=subprocess.Popen(['dotnet',str(p/'Api.dll')],cwd=p,env=env,stdout=streams[0],stderr=streams[1])
 save(d/'deployment.json',{'candidate':which,'package_sha256':expected,'fake_receiver_status':status,'target':'same local loopback port; stop/start, no load balancer'})
 deadline=time.monotonic()+20
 while True:
  try:
   code,v=request('GET','/health')
   if code==200:break
  except OSError:pass
  if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('startup failed')
  time.sleep(.1)
 check(label+'-version',v['version']==(p/'VERSION').read_text().strip(),v)
 return d
def cancel(order):
 request('POST','/orders',dict(id=order,paid=True,shipped=False))
 code,v=request('POST',f'/orders/{order}/cancel')
 check(phase+'-cancel',code==200 and v['transitioned'] and v['refund_requested'],v)
 return v['notification_id']
def terminal(d,nid):
 deadline=time.monotonic()+10
 while True:
  p=d/'logs.jsonl';logs=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
  found=[x for x in logs if x.get('notification_id')==nid and x.get('event') in ['notify_sent','notify_dead_letter']]
  if found:return found[-1]
  if time.monotonic()>deadline:raise RuntimeError('notification terminal timeout')
  time.sleep(.05)
try:
 old=start(a.old,'before',200);nid=cancel('before-update');check('before-sent',terminal(old,nid)['event']=='notify_sent',nid)
 new=start(a.new,'updated',503)
 code,v=request('GET','/version');check('new-endpoint',code==200 and v['notification_mode']=='async',v)
 code,v=request('GET','/orders/before-update');check('update-loses-memory-state',code==404,code)
 nid=cancel('during-update');end=terminal(new,nid);check('failure-detected',end['event']=='notify_dead_letter',end)
 failed=[x for x in receipts if x['payload']['notification_id']==nid]
 check('failure-four-attempts',len(failed)==4 and all(x['status']==503 for x in failed),len(failed))
 save(o/'incident.json',{'event':'notification_delivery_failed','notification_id':nid,'order_id':'during-update','candidate':a.new,'observed':end,'attempts':len(failed),'api_cancel_status':200,'receiver_status':503,'cause':'deliberately injected fake receiver failure, not a newly discovered program defect','action':'stop update and restore previous package plus healthy receiver; do not replay failed order','owner':'author performing local operator role','acceptance':'service restored and unresolved order explicitly retained'})
 restored=start(a.old,'rolled-back',200)
 code,v=request('GET','/version');check('old-endpoint-restored',code==404,code)
 code,v=request('GET','/orders/during-update');check('rollback-does-not-restore-orders',code==404,code)
 rid=cancel('after-rollback');check('restored-sent',terminal(restored,rid)['event']=='notify_sent',rid)
 check('failed-order-not-replayed',not any(x['phase']=='rolled-back' and x['payload']['order_id']=='during-update' for x in receipts),'no automatic replay')
except Exception as e:check('runner',False,repr(e))
finally:
 stop();sink.shutdown();sink.server_close()
 save(o/'requests.json',events);save(o/'receipts.json',receipts)
 report={'passed':bool(checks) and all(x['passed'] for x in checks),'checks':checks,'old_candidate':a.old,'new_candidate':a.new,'limits':'author-operated local rehearsal, no production deployment; receiver failure injected; in-memory state lost; failed business event unresolved'}
 save(o/'report.json',report)
print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['passed'] else 1)
