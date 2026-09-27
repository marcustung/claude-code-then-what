"""Local HTTP concurrency and trace lab. Does not modify historical evidence."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,http.server,json,os,socket,subprocess,threading,time,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parent

def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('version',choices=['baseline','fixed','release-next']);ap.add_argument('name');ap.add_argument('--mode',choices=['concurrent','trace'],default='concurrent');ap.add_argument('--delay-ms',type=int,default=50);ap.add_argument('--sink-status',type=int,default=200);ns=ap.parse_args()
 if not ns.name.replace('-','').replace('_','').isalnum():ap.error('use a new simple run name')
 out=ROOT/'runs'/ns.name;out.mkdir(exist_ok=False);src=ROOT/ns.version
 received=[];calls=[];guard=threading.Lock();checks=[];proc=None;start=time.monotonic()
 def check(name,ok,detail):checks.append(dict(name=name,pass_=bool(ok),detail=detail))
 class Sink(http.server.BaseHTTPRequestHandler):
  def do_POST(self):
   payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
   with guard:received.append(dict(payload=payload,status=ns.sink_status))
   self.send_response(ns.sink_status);self.end_headers();self.wfile.write(b'{}')
  def log_message(self,*a):pass
 sink=http.server.ThreadingHTTPServer(('127.0.0.1',0),Sink);threading.Thread(target=sink.serve_forever,daemon=True).start()
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 def request(method,path,body=None,rid=None):
  headers={'Content-Type':'application/json','X-Actor':'teaching-test','X-Run-Id':ns.name,'X-Request-Id':rid or ns.name+'-setup'}
  req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,method=method,headers=headers,data=json.dumps(body).encode() if body is not None else None)
  try:
   with urllib.request.urlopen(req,timeout=10) as res:code=res.status;data=json.load(res)
  except urllib.error.HTTPError as e:code=e.code;data=json.loads(e.read())
  with guard:calls.append(dict(method=method,path=path,request_id=headers['X-Request-Id'],status=code,response=data))
  return code,data
 stdout=(out/'stdout.txt').open('w');stderr=(out/'stderr.txt').open('w')
 try:
  b=subprocess.run(['dotnet','build','src/Api/Api.csproj','--nologo'],cwd=src,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
  (out/'build.txt').write_text(b.stdout+b.stderr,encoding='utf-8');check('build',b.returncode==0,b.returncode)
  if b.returncode:raise RuntimeError('build failed')
  env=os.environ.copy();env.pop('OC_FAULTS',None);env.update(ASPNETCORE_URLS=f'http://127.0.0.1:{port}',OC_RUN_DIR=str(out),OC_SINK_URL=f'http://127.0.0.1:{sink.server_port}/notify',OC_TEST_DELAY_MS=str(ns.delay_ms))
  proc=subprocess.Popen(['dotnet','src/Api/bin/Debug/net9.0/Api.dll'],cwd=src,env=env,stdout=stdout,stderr=stderr)
  deadline=time.monotonic()+20
  while True:
   try:
    if request('GET','/ready')[0]==200:break
   except (OSError,urllib.error.URLError):pass
   if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('startup failed')
   time.sleep(.1)
  rounds=20 if ns.mode=='concurrent' else 1;workers=8 if ns.mode=='concurrent' else 1
  for i in range(rounds):
   oid=f'order-{i:02d}';request('POST','/orders',dict(id=oid,paid=True,shipped=False))
   barrier=threading.Barrier(workers)
   def cancel(j):barrier.wait(timeout=10);return request('POST',f'/orders/{oid}/cancel',rid=f'{ns.name}-{i:02d}-{j:02d}')
   with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:responses=list(pool.map(cancel,range(workers)))
   changed=sum(v.get('transitioned') is True for _,v in responses);refunds=sum(v.get('refund_requested') is True for _,v in responses)
   check(oid+'-transitions',all(c==200 for c,_ in responses) and changed==1 and refunds==1,dict(changed=changed,refunds=refunds,requests=workers))
   _,state=request('GET',f'/orders/{oid}');check(oid+'-state',state['order']['cancelled'],state)
   c,v=request('POST',f'/orders/{oid}/cancel',rid=f'{ns.name}-{i:02d}-repeat');check(oid+'-repeat',c==200 and not v['transitioned'] and not v['refund_requested'],v)
  # Wait for terminal worker events, bounded. A receipt is not an acknowledgement.
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   lp=out/'logs.jsonl';logs=[json.loads(l) for l in lp.read_text(encoding='utf-8').splitlines()] if lp.exists() else []
   terminals=[x for x in logs if x.get('event') in ['notify_sent','notify_dead_letter']]
   expected=sum(x['response'].get('transitioned',False) for x in calls if x['method']=='POST' and x['path'].endswith('/cancel'))
   if len(terminals)>=expected:break
   time.sleep(.1)
  time.sleep(.3)
  for i in range(rounds):
   oid=f'order-{i:02d}';items=[x['payload'] for x in received if x['payload']['order_id']==oid];ids={x['notification_id'] for x in items}
   check(oid+'-one-notification',len(ids)==1,dict(distinct_notifications=len(ids),http_attempts=len(items)))
  if ns.mode=='trace':
   logs=[json.loads(l) for l in (out/'logs.jsonl').read_text(encoding='utf-8').splitlines()];first=next(x for x in calls if x['response'].get('transitioned'));rid=first['request_id'];nid=first['response'].get('notification_id')
   terminal=[x for x in logs if x.get('notification_id')==nid and x.get('event') in ['notify_sent','notify_dead_letter']]
   want='notify_sent' if ns.sink_status==200 else 'notify_dead_letter'
   check('correlation',bool(nid) and any(x.get('request_id')==rid and x.get('notification_id')==nid for x in logs if x.get('event')=='cancel') and len(terminal)==1 and terminal[0]['event']==want,dict(request_id=rid,notification_id=nid,terminal=terminal))
   check('attempts',len(received)==(1 if ns.sink_status==200 else 4),len(received))
 except Exception as e:check('runner',False,repr(e))
 finally:
  if proc:
   proc.terminate()
   try:proc.wait(timeout=5)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
  sink.shutdown();sink.server_close();stdout.close();stderr.close();save(out/'requests.json',calls);save(out/'receipts.json',received)
  report=dict(version=ns.version,mode=ns.mode,delay_ms=ns.delay_ms,sink_status=ns.sink_status,checks=checks,passed=bool(checks) and all(c['pass_'] for c in checks),elapsed_seconds=time.monotonic()-start,source_sha256={str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (src/'src').rglob('*.cs') if 'obj' not in p.parts},limits='single process, memory store, loopback, bounded observation; no crash recovery, real auth/payment, throughput SLA or exactly-once guarantee')
  save(out/'report.json',report)
 print(json.dumps(dict(run=ns.name,passed=report['passed'],checks=len(checks),failures=sum(not c['pass_'] for c in checks))))
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
