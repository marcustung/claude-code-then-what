from pathlib import Path
import argparse,datetime,hashlib,http.server,json,os,socket,subprocess,threading,time,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parent

def free_port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('--artifact',type=Path);ns=ap.parse_args()
 if not ns.name.replace('-','').replace('_','').isalnum():ap.error('simple run name required')
 out=ROOT/'runs'/ns.name;out.mkdir(exist_ok=False);out=out.resolve();started=time.monotonic();checks=[];calls=[];received=[];lock=threading.Lock()
 def check(name,ok,detail):checks.append({'name':name,'pass':bool(ok),'detail':detail})
 class Sink(http.server.BaseHTTPRequestHandler):
  def do_POST(self):
   obj=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
   with lock:received.append(obj)
   self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"ok":true}')
  def log_message(self,*args):pass
 sink=http.server.ThreadingHTTPServer(('127.0.0.1',0),Sink);threading.Thread(target=sink.serve_forever,daemon=True).start();apiport=free_port()
 env=os.environ.copy();env.update({'ASPNETCORE_URLS':f'http://127.0.0.1:{apiport}','OC_RUN_DIR':str(out),'OC_SINK_URL':f'http://127.0.0.1:{sink.server_port}/notify'});env.pop('OC_FAULTS',None)
 exe=ns.artifact.resolve()/'Api.dll' if ns.artifact else ROOT/'src/Api/bin/Debug/net9.0/Api.dll'
 stdout=(out/'stdout.txt').open('w',encoding='utf-8');stderr=(out/'stderr.txt').open('w',encoding='utf-8');proc=None
 def request(method,path,body=None,actor='demo-reader'):
  data=json.dumps(body).encode() if body is not None else None
  headers={'Content-Type':'application/json','X-Run-Id':ns.name,'X-Request-Id':f'{ns.name}-{len(calls)+1}'}
  if actor:headers['X-Actor']=actor
  req=urllib.request.Request(f'http://127.0.0.1:{apiport}'+path,data=data,headers=headers,method=method)
  try:
   with urllib.request.urlopen(req,timeout=3) as res:code=res.status;result=json.load(res)
  except urllib.error.HTTPError as e:code=e.code;result=json.loads(e.read())
  calls.append({'method':method,'path':path,'body':body,'status':code,'response':result,'request_id':headers['X-Request-Id']});return code,result
 try:
  if not ns.artifact:
   b=subprocess.run(['dotnet','build','src/Api/Api.csproj','--nologo'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
   (out/'build.txt').write_text(b.stdout+b.stderr,encoding='utf-8');check('build',b.returncode==0,b.returncode)
   if b.returncode:raise RuntimeError('build failed')
  proc=subprocess.Popen(['dotnet',str(exe)],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
  deadline=time.monotonic()+20
  while True:
   try:
    if request('GET','/ready')[0]==200:break
   except (OSError,urllib.error.URLError):pass
   if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('API not ready')
   time.sleep(.1)
  for id,paid,shipped in [('paid',True,False),('unpaid',False,False),('shipped',True,True)]:request('POST','/orders',{'id':id,'paid':paid,'shipped':shipped})
  for id,status,flag,transition in [('paid',200,True,True),('paid',200,False,False),('unpaid',200,False,True),('shipped',409,False,False)]:
   code,data=request('POST',f'/orders/{id}/cancel');check(f'{id}-response-{len(checks)}',code==status and data.get('refund_requested')==flag and data.get('transitioned')==transition,{'status':code,'body':data})
  code,data=request('POST','/orders/paid/cancel',actor=None);check('no-demo-actor',code==401,code)
  for id,cancelled in [('paid',True),('unpaid',True),('shipped',False)]:
   code,data=request('GET',f'/orders/{id}');check(id+'-state',code==200 and data['order']['cancelled']==cancelled,data)
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   with lock:
    if len(received)>=2:break
   time.sleep(.1)
  time.sleep(.4)
  with lock:payload=list(received)
  check('notification-ids-and-flags',sorted((x.get('order_id'),x.get('refund_requested')) for x in payload)==[('paid',True),('unpaid',False)],payload)
  logs=[json.loads(l) for l in (out/'logs.jsonl').read_text(encoding='utf-8-sig').splitlines()]
  rows=[x for x in logs if x.get('event')=='cancel' and x.get('order_id')=='paid' and x.get('result') in ['ok','idempotent']]
  check('paid-log-first-and-repeat',[x.get('refund_requested') for x in rows]==[True,False],rows)
 except Exception as e:check('runner',False,type(e).__name__+': '+str(e))
 finally:
  if proc:
   proc.terminate()
   try:proc.wait(timeout=5)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
  sink.shutdown();sink.server_close();stdout.close();stderr.close()
  (out/'requests.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2),encoding='utf-8');(out/'payloads.json').write_text(json.dumps(received,ensure_ascii=False,indent=2),encoding='utf-8')
  report={'checks':checks,'pass':bool(checks) and all(c['pass'] for c in checks),'elapsed_seconds':time.monotonic()-started,'human_minutes':None,'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').rglob('*.cs') if 'obj' not in p.parts},'artifact_sha256':hashlib.sha256(exe.read_bytes()).hexdigest() if exe.exists() else None,'limits':'Loopback, sequential requests, bounded observation. Test receiver captures payload; no real payment, production auth, concurrent exactly-once, restart recovery or remote deployment proof.'}
  (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'run':ns.name,'checks':len(checks),'pass':report['pass']},ensure_ascii=False));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
