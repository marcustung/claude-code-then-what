from pathlib import Path
import argparse,datetime,hashlib,http.server,json,os,secrets,shutil,socket,subprocess,threading,time,urllib.request,urllib.parse
L=Path(__file__).resolve().parent
CASES=('complete','missing-receipts','query-failure')
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
def hashes(p):return {str(f.relative_to(p)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file() and '__pycache__' not in str(f)}
def request_json(url,body=None,headers=None):
 req=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers=headers or {})
 with urllib.request.urlopen(req,timeout=10) as f:return f.status,json.loads(f.read() or '{}')
def wait(url,timeout=65):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  try:
   with urllib.request.urlopen(url,timeout=2) as f:
    if f.status==200:return
  except OSError:pass
  time.sleep(.5)
 raise RuntimeError('not ready: '+url)
def free_port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def prepare(name,package):
 out=L/'runs'/name;out.mkdir(parents=True,exist_ok=False)
 feed=out/'feed';feed.mkdir()
 package=package.resolve();delivery=package.parents[2]
 expected=json.loads((package.parent/'package-manifest.json').read_text(encoding='utf-8-sig'))
 expected={k.replace('\\','/'):v for k,v in expected.items()}
 if hashes(package)!=expected:raise RuntimeError('r2 package hash mismatch')
 if not json.loads((package.parent/'report.json').read_text(encoding='utf-8-sig'))['passed']:raise RuntimeError('candidate not passed')
 save(out/'package-manifest.json',expected)
 version=(package/'VERSION').read_text().strip()
 images={}
 for image in ['grafana/loki:3.5.0','grafana/grafana:12.0.2','grafana/alloy:v1.8.3','grafana/mcp-grafana:latest']:
  d=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True,encoding='utf-8'))[0]
  images[image]={'id':d['Id'],'repo_digests':d['RepoDigests']}
 save(out/'images.json',images)
 mcp_image=images['grafana/mcp-grafana:latest']['repo_digests'][0]
 env=os.environ.copy();env.update(DAY17_ADMIN_PASSWORD=secrets.token_urlsafe(32),DAY17_FEED=str(feed))
 subprocess.run(['docker','compose','-f',str(L/'compose.yaml'),'up','-d'],cwd=L,env=env,check=True)
 wait('http://127.0.0.1:3217/api/health');wait('http://127.0.0.1:3117/ready')
 states=[]
 for case in CASES:
  d=feed/case;(d/'api').mkdir(parents=True);(d/'receiver').mkdir()
  for f in [d/'api/logs.jsonl',d/'receiver/logs.jsonl']:f.touch()
  start=now();oid=f'{name}-{case}';receipts=[]
  class Receiver(http.server.BaseHTTPRequestHandler):
   def do_POST(self):
    payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
    item={'ts':now(),'event':'notification_received',**payload};receipts.append(item)
    # Keep ground truth outside the model workspace; omit receiver collection for missing-evidence case.
    if case!='missing-receipts':
     with (d/'receiver/logs.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(item)+'\n')
    self.send_response(200);self.end_headers();self.wfile.write(b'{}')
   def log_message(self,*args):pass
  sink=http.server.ThreadingHTTPServer(('127.0.0.1',0),Receiver)
  threading.Thread(target=sink.serve_forever,daemon=True).start()
  base=f'http://127.0.0.1:{free_port()}'
  appenv=os.environ.copy()
  for key in ['OC_FAULTS','OC_TEST_DELAY_MS']:appenv.pop(key,None)
  appenv.update(ASPNETCORE_URLS=base,OC_RUN_DIR=str(d/'api'),OC_SINK_URL=f'http://127.0.0.1:{sink.server_port}/notify')
  with (d/'stdout.txt').open('w') as stdout,(d/'stderr.txt').open('w') as stderr:
   app=subprocess.Popen(['dotnet',str(package/'Api.dll')],cwd=package,env=appenv,stdout=stdout,stderr=stderr)
   try:
    wait(base+'/health',20);_,v=request_json(base+'/version');assert v['version']==version
    headers={'Content-Type':'application/json','X-Actor':'day17-lab','X-Request-Id':oid,'X-Run-Id':name}
    created=request_json(base+'/orders',{'id':oid,'paid':True,'shipped':False},headers)
    cancelled=request_json(base+'/orders/'+oid+'/cancel',{},headers);assert cancelled[0]==200
    until=time.monotonic()+15
    while time.monotonic()<until:
     logs=(d/'api/logs.jsonl').read_text(encoding='utf-8')
     if receipts and 'notify_sent' in logs:break
     time.sleep(.1)
    assert receipts and 'notify_sent' in logs
    save(out/'audit'/f'{case}.json',{'order_id':oid,'created':created,'cancelled':cancelled,'receiver_ground_truth':receipts,'version_response':v,'receiver_collection_enabled':case!='missing-receipts'})
   finally:
    app.terminate()
    try:app.wait(timeout=8)
    except subprocess.TimeoutExpired:app.kill();app.wait()
    sink.shutdown();sink.server_close()
  end=now();start=datetime.datetime.fromisoformat(start.replace('Z','+00:00')).replace(microsecond=0).isoformat().replace('+00:00','Z');end=(datetime.datetime.fromisoformat(end.replace('Z','+00:00')).replace(microsecond=0)+datetime.timedelta(seconds=1)).isoformat().replace('+00:00','Z');workspace=out/'workspaces'/case;workspace.mkdir(parents=True)
  skill=workspace/'.claude/skills/trace-notification/SKILL.md';skill.parent.mkdir(parents=True)
  shutil.copy2(L.parent/'package/.claude/skills/trace-notification/SKILL.md',skill)
  for dest,src in [('src/Program.cs',delivery/'day16-design-trace-01/workspace/src/Program.cs'),('src/Cancellation.cs',delivery/'day16-design-trace-01/workspace/src/Cancellation.cs'),('design/design-review.md',delivery/'day16-design-trace-01/workspace/design-input/design-review.md')]:
   target=workspace/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
  task={'order_id':oid,'version':version,'environment':'local Docker teaching lab','time_start':start,'time_end':end,'datasource_uid':'day17-unavailable' if case=='query-failure' else 'day17-loki','labels':{'lab_case':case},'services':['order-api','notification-receiver'],'log_access':'Grafana MCP only; raw logs and ground truth are outside this workspace','scope':'Use only the assigned datasource and lab_case; do not switch sources when a query fails.'}
  plugin=workspace/'plugin';(plugin/'.claude-plugin').mkdir(parents=True)
  save(plugin/'.claude-plugin/plugin.json',{'name':'day17-trace','version':'0.1.1','description':'Teaching trace skill'})
  dest=plugin/'skills/trace-notification/SKILL.md';dest.parent.mkdir(parents=True)
  shutil.copy2(L/'skill/SKILL.md',dest)
  save(workspace/'task.json',task)
  save(workspace/'mcp.json',{'mcpServers':{'grafana':{'command':'docker','args':['run','--rm','-i','--network','ironman-day17-log','-e','GRAFANA_URL=http://grafana:3000',mcp_image,'--disable-write','--enabled-tools','datasource,loki','--max-loki-log-limit','30','--transport','stdio']}}})
  states.append(task)
 save(out/'tasks.json',states)
 checks=[]
 for task in states:
  case=task['labels']['lab_case']
  for service in task['services']:
   q='{service_name="'+service+'",lab_case="'+case+'"} | json | order_id="'+task['order_id']+'"'
   params=urllib.parse.urlencode({'query':q,'start':task['time_start'],'end':task['time_end'],'limit':30})
   want=0 if case=='missing-receipts' and service=='notification-receiver' else (2 if service=='order-api' else 1)
   until=time.monotonic()+40
   while True:
    _,res=request_json('http://127.0.0.1:3117/loki/api/v1/query_range?'+params)
    count=sum(len(v['values']) for v in res['data']['result'])
    if count==want or time.monotonic()>until:break
    time.sleep(1)
   checks.append({'case':case,'service':service,'query':q,'expected_lines':want,'actual_lines':count,'passed':count==want,'response':res})
 save(out/'ingestion-checks.json',checks);assert all(c['passed'] for c in checks),'ingestion failed'
 save(out/'provenance.json',{'run':name,'started_at':states[0]['time_start'],'package_version':version,'package_source':'sdlc-delivery/runs/acceptance-next-01/package','live_requests':True,'replayed_historical_logs':False,'originals_modified':False,'model_runs_complete':False})
 print('PREPARED '+name+'; ingestion 6/6; Grafana http://127.0.0.1:3217')
def model(name,case,attempt):
 out=L/'runs'/name;workspace=out/'workspaces'/case;records=out/'model'/attempt/case;records.mkdir(parents=True,exist_ok=False)
 prompt='''請使用 day17-trace:trace-notification Skill，查核 task.json 指定的通知事件。先載入 Skill，再讀本次任務與部署版本的程式、設計。
Log 只能透過提供的 Grafana MCP 查詢。依 task.json 的 datasource_uid、lab_case、服務與時間窗查詢；先用 order_id 找 notification_id，再核對接收端。不要查其他資料來源或其他事件。
逐項附查詢條件與來源，最後依 Skill 輸出 JSON。唯讀，不修改檔案，不執行 shell，不補送、不結案。工具失敗時保留實際錯誤與下一步，不自行擴大範圍。繁體中文，最多 900 字。'''
 (records/'prompt.txt').write_text(prompt,encoding='utf-8');before=hashes(workspace);save(records/'input-manifest.json',before)
 allowed='Read,Grep,Glob,Skill,mcp__grafana__list_datasources,mcp__grafana__get_datasource,mcp__grafana__query_loki_logs,mcp__grafana__list_loki_label_names,mcp__grafana__list_loki_label_values,mcp__grafana__query_loki_stats'
 cmd=[str(Path.home()/'.local/bin/claude.exe'),'-p',prompt,'--model','sonnet','--effort','medium','--restricted','--tools','Read,Grep,Glob,Skill','--allowedTools',allowed,'--plugin-dir',str(workspace/'plugin'),'--setting-sources','project','--strict-mcp-config','--mcp-config',str(workspace/'mcp.json'),'--output-format','stream-json','--verbose','--no-session-persistence','--max-budget-usd','3']
 save(records/'command.json',cmd);t=time.monotonic()
 with (records/'trace.jsonl').open('w',encoding='utf-8') as stdout,(records/'stderr.txt').open('w',encoding='utf-8') as stderr:
  try:result=subprocess.run(cmd,cwd=workspace,stdout=stdout,stderr=stderr,timeout=420);code=result.returncode
  except subprocess.TimeoutExpired:code=124
 calls=[];results=[];final={}
 for line in (records/'trace.jsonl').read_text(encoding='utf-8').splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  message=e.get('message')
  if not isinstance(message,dict):message={}
  for b in message.get('content',[]) or []:
   if not isinstance(b,dict):continue
   if b.get('type')=='tool_use':calls.append(b)
   if b.get('type')=='tool_result':results.append(b)
  if e.get('type')=='result':final=e
 save(records/'tool-calls.json',calls);save(records/'tool-results.json',results);save(records/'result.json',final)
 (records/'answer.md').write_text(final.get('result',''),encoding='utf-8')
 after=hashes(workspace);changed=[f for f in set(before)|set(after) if before.get(f)!=after.get(f)]
 summary={'exit':code,'seconds':round(time.monotonic()-t,2),'turns':final.get('num_turns'),'cost_usd':final.get('total_cost_usd'),'changed':changed,'skill_calls':sum(x.get('name')=='Skill' for x in calls),'query_calls':sum(x.get('name')=='mcp__grafana__query_loki_logs' for x in calls),'tool_names':sorted(set(x.get('name','') for x in calls))}
 save(records/'execution.json',summary);print(json.dumps(summary))
 if code or not summary['query_calls']:raise SystemExit(1)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','model']);ap.add_argument('name');ap.add_argument('case',nargs='?',choices=CASES);ap.add_argument('--attempt',default='r2');ap.add_argument('--package',type=Path,default=(L.parents[1]/'sdlc-delivery/runs/acceptance-next-01/package' if (L.parents[1]/'sdlc-delivery').exists() else L.parents[2]/'day14/lab-delivery/runs/acceptance-next-01/package'));a=ap.parse_args()
 if not all(x.replace('-','').replace('_','').isalnum() for x in [a.name,a.attempt]):ap.error('simple run name required')
 if a.action=='prepare':prepare(a.name,a.package)
 else:
  if not a.case:ap.error('case required')
  model(a.name,a.case,a.attempt)