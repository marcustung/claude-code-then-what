from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime,json,os,subprocess,time,urllib.request,urllib.error,socket,math,hashlib,platform
R=Path(__file__).resolve().parent
RUN=R/'runs'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
RUN.mkdir(parents=True)
API=R/'service/src/Api/bin/Release/net9.0/Api.dll'
SINK=R/'service/src/FakeSink/bin/Release/net9.0/FakeSink.dll'
STACK=Path.home()/'day26-diagnostics-tools/dotnet-stack.exe'
N=384; C=96

def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def req(base,path,data=None,auth=True):
 headers={'Content-Type':'application/json'}
 if auth:headers['X-Actor']='teaching-user'
 q=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
 try:
  with urllib.request.urlopen(q,timeout=30) as f:return f.status,json.load(f)
 except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
def ready(base,proc):
 for _ in range(100):
  if proc.poll() is not None:raise RuntimeError('service exited')
  try:
   if req(base,'/health')[0]==200:return
  except Exception:pass
  time.sleep(.1)
 raise RuntimeError('startup timeout')
def percentile(xs,q):return sorted(xs)[max(0,math.ceil(len(xs)*q)-1)]
def one(mode,idx,diagnostic=False):
 d=RUN/f'{idx}-{mode}';d.mkdir()
 ap,sp=port(),port();ab=f'http://127.0.0.1:{ap}';sb=f'http://127.0.0.1:{sp}'
 procs=[];files=[]
 try:
  for label,dll,url,extra in [('sink',SINK,sb,{}),('api',API,ab,{'OC_SINK_URL':sb+'/notify','LAB_WAIT_MODE':mode,'DOTNET_PROCESSOR_COUNT':'2'})]:
   rd=d/label;rd.mkdir()
   env={**os.environ,'ASPNETCORE_URLS':url,'OC_RUN_DIR':str(rd),**extra}
   # Explicitly remove unrelated experiment fault settings from this child only.
   for k in ['DOTNET_GCHeapHardLimit','COMPlus_GCHeapHardLimit','OC_SINK_DELAY_MS']:env.pop(k,None)
   out=(d/(label+'-stdout.txt')).open('w');files.append(out)
   p=subprocess.Popen(['dotnet',str(dll)],env=env,cwd=R,stdout=out,stderr=subprocess.STDOUT);procs.append(p)
   ready(url,p)
  for i in range(3):
   oid=f'warm-{i}';req(ab,'/orders',{'id':oid,'paid':True});assert req(ab,f'/orders/{oid}/cancel',{})[0]==200
  for i in range(N):assert req(ab,'/orders',{'id':f'load-{i}','paid':True})[0]==200
  def cancel(i):
   start=time.perf_counter()
   try:status,body=req(ab,f'/orders/load-{i}/cancel',{})
   except Exception as e:status,body=0,{'error':str(e)}
   return {'id':f'load-{i}','status':status,'body':body,'latency_ms':(time.perf_counter()-start)*1000}
  started=time.time();begin=time.perf_counter()
  with ThreadPoolExecutor(max_workers=C) as pool:
   futures=[pool.submit(cancel,i) for i in range(N)]
   if diagnostic:
    time.sleep(.6)
    with (d/'stacks.txt').open('w',encoding='utf-8') as f:
     s=subprocess.run([str(STACK),'report','--process-id',str(procs[1].pid)],stdout=f,stderr=subprocess.STDOUT,timeout=30)
    (d/'stack-exit.txt').write_text(str(s.returncode))
   rows=[f.result(timeout=120) for f in futures]
  end=time.time();elapsed=time.perf_counter()-begin
  (d/'requests.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
  state_ok=all(req(ab,f'/orders/load-{i}')[1]['order']['cancelled'] for i in range(N))
  for _ in range(100):
   receipts=req(sb,'/receipts')[1]
   if receipts['received']>=N+3:break
   time.sleep(.1)
  before=receipts.copy()
  duplicate=req(ab,'/orders/load-0/cancel',{})
  req(ab,'/orders',{'id':'shipped','shipped':True,'paid':True})
  shipped=req(ab,'/orders/shipped/cancel',{})
  unauthorized=req(ab,'/orders/load-0/cancel',{},False)
  missing=req(ab,'/orders/absent/cancel',{})
  time.sleep(.6)
  after=req(sb,'/receipts')[1]
  recs=[json.loads(l) for l in (d/'sink/receipts.jsonl').read_text().splitlines()]
  ids=[r['order_id'] for r in recs if r['order_id'].startswith('load-')]
  metrics=[json.loads(l) for l in (d/'api/runtime.jsonl').read_text().splitlines()]
  window=[m for m in metrics if started<=datetime.datetime.fromisoformat(m['ts']).timestamp()<=end]
  checks={'all_http_200':all(r['status']==200 for r in rows),'all_transitioned':all(r['body'].get('transitioned') is True for r in rows),
   'refund_preserved':all(r['body'].get('refund_requested') is True for r in rows),'states_cancelled':state_ok,
   'exact_receiver_order_ids':len(ids)==N and set(ids)=={f'load-{i}' for i in range(N)},'no_duplicate_notifications':after['duplicates']==0,
   'idempotent':duplicate[0]==200 and duplicate[1]['transitioned'] is False and duplicate[1]['refund_requested'] is False,
   'shipped_409':shipped[0]==409,'unauthorized_401':unauthorized[0]==401,'missing_404':missing[0]==404,'no_extra_receipts':before==after}
  lat=[r['latency_ms'] for r in rows]
  summary={'mode':mode,'diagnostic':diagnostic,'request_count':N,'concurrency':C,'elapsed_s':round(elapsed,3),'p50_ms':round(percentile(lat,.5),1),
   'p95_ms':round(percentile(lat,.95),1),'max_ms':round(max(lat),1),'http_200':sum(r['status']==200 for r in rows),
   'thread_peak':max(m['threads'] for m in window),'pending_peak':max(m['pending'] for m in window),
   'cpu_core_percent_mean':round(sum(m['cpu_core_percent'] for m in window)/len(window),1),
   'heap_peak_mb':round(max(m['gc_heap_bytes'] for m in window)/2**20,1),'receipts':after,'checks':checks,
   'load_start_epoch':started,'load_end_epoch':end,'dll_sha256':hashlib.sha256(API.read_bytes()).hexdigest()}
  (d/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
  print(json.dumps(summary),flush=True)
  return summary
 finally:
  for p in reversed(procs):
   if p.poll() is None:
    p.terminate()
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:p.kill();p.wait()
  for f in files:f.close()

summaries=[]
for idx,mode in enumerate(['blocking','async','async','blocking']):summaries.append(one(mode,idx))
summaries.append(one('blocking',4,True))
(RUN/'summary.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
(R/'latest.txt').write_text(str(RUN.relative_to(R)),encoding='utf-8')
(RUN/'environment.json').write_text(json.dumps({'platform':platform.platform(),'dotnet':subprocess.run(['dotnet','--version'],capture_output=True,text=True).stdout.strip(),'api_sha256':hashlib.sha256(API.read_bytes()).hexdigest(),'processor_hint':2,'actual_cpu_quota':None,'external_claude_called':False},indent=2),encoding='utf-8')
print('DONE '+str(RUN),flush=True)
