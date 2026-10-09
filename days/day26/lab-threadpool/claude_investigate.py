from pathlib import Path
from datetime import datetime,timezone
import os,json,subprocess,time,shutil,runpy
from collections import Counter
R=Path(__file__).resolve().parent;WS=Path((R/'workspace.txt').read_text());D=R/(R/'latest-blind.txt').read_text()
W=R/'claude-a'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');W.mkdir(parents=True)
(WS/'evidence').mkdir(exist_ok=True)
summary=json.loads((D/'0-incident/summary.json').read_text());requests=json.loads((D/'0-incident/requests.json').read_text())
client={'planned':384,'concurrency':96,'http_status_counts':dict(Counter(str(x['status']) for x in requests)),'latency_p95_ms':summary['p95_ms'],'p95_definition':'client elapsed until HTTP response or exception; timeout30s','errors':dict(Counter(x['body'].get('error','') for x in requests if x['status']==0))}
(WS/'evidence/client-summary.json').write_text(json.dumps(client,indent=2),encoding='utf-8')
shutil.copy2(D/'1-incident/stacks.txt',WS/'evidence/stacks.txt')
subprocess.run(['python',str(R/'replay_for_claude.py')],check=True);time.sleep(8)
win=json.loads((R/'replay-window-threadpool.json').read_text())
conf={'mcpServers':{'investigation':{'command':'python','args':[str(R/'readonly_mcp.py')],'env':{'LAB_SOURCE_ROOT':str(WS),'LAB_GCX_ADAPTER':str(R.parent/'day24-observability-lab/gcx_readonly_mcp.py'),'GCX_CONFIG':str(Path(os.environ['TEMP'])/'day24-gcx-private.yaml'),'DAY24_TOOL_AUDIT':str(W/'tool-audit.jsonl'),'PYTHONUTF8':'1'}}}}
(W/'mcp.json').write_text(json.dumps(conf),encoding='utf-8')
prompt=f'''你是值班工程師，只調查此教學訂單服務，不修改。症狀：384筆取消、96併發，有些請求很慢，部分客戶端連線失敗。根因未提供。
工具只有query_observability與read_project。先提出至少兩個可區分假設及推翻條件，再查資料，依證據改判斷。不要只找可疑程式就下結論。
Grafana是原始紀錄的時間平移重放，不是即時事故。時間{win['start']}到{win['end']}；job="{win['job']}"。
Prometheus指標：oc_tp_threads、oc_tp_pending、oc_tp_completed、oc_cpu_core_percent、oc_gc_heap_bytes。cpu_core_percent是相對單一核心的百分比，不是整台主機；completed為累計值，其他是gauge。請查區間或時間序列，不只看一個點。查時間序列用operation=metrics_range，start/end用上面時間，工具固定1秒step；metrics是單點查詢。
Loki service_name="{win['job']}"。read_project可讀src/Api/Program.cs、src/Domain/Cancellation.cs、specs/requirements.md、evidence/client-summary.json、evidence/stacks.txt。
stacks.txt為同版程式另外一輪診斷取樣，不能混入計時比較；read_project支援start_line與max_lines（最多120），需要時分頁讀。處理器提示2，非OS CPU quota。
最後用繁體中文給：至少兩個假設及推翻條件、查詢/檔案行號、支持/排除/未知、最可能原因、最小修法與風險、修完如何驗證。未提供驗證工具就列缺件，不編路徑。不得宣稱已修改或重跑。'''
shutil.copy2(R/'readonly_mcp.py',W/'adapter-v2.py')
(W/'prompt.txt').write_text(prompt,encoding='utf-8')
schema=runpy.run_path(str(R.parent/'day26-live-lab/run_a.py'))['SCHEMA']
args=['claude','-p','--model','sonnet','--tools','','--allowedTools','mcp__investigation__query_observability,mcp__investigation__read_project','--strict-mcp-config','--mcp-config',str(W/'mcp.json'),'--setting-sources','project','--settings',json.dumps({'disableAllHooks':True,'autoMemoryEnabled':False}),'--no-session-persistence','--output-format','stream-json','--verbose','--json-schema',json.dumps(schema)]
t=time.time()
with (W/'trace.jsonl').open('w',encoding='utf-8') as out,(W/'stderr.txt').open('w',encoding='utf-8') as err:
 p=subprocess.run(args,input=prompt,cwd=WS,stdout=out,stderr=err,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},timeout=600)
res={}
for line in (W/'trace.jsonl').read_text(encoding='utf-8').splitlines():
 try:
  x=json.loads(line)
  if x.get('type')=='result':res=x
 except ValueError:pass
(W/'card.json').write_text(json.dumps(res.get('structured_output',{}),ensure_ascii=False,indent=2),encoding='utf-8')
(W/'execution.json').write_text(json.dumps({'exit':p.returncode,'seconds':round(time.time()-t,1),'cost_usd':res.get('total_cost_usd'),'turns':res.get('num_turns'),'subtype':res.get('subtype'),'model':'sonnet','window':win},indent=2),encoding='utf-8')
(R/'latest-claude-a.txt').write_text(str(W.relative_to(R)),encoding='utf-8')
print('DONE',W,p.returncode,res.get('total_cost_usd'),res.get('num_turns'))
