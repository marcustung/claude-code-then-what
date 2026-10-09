from pathlib import Path
from datetime import datetime,timezone
import json,os,shutil,subprocess,time,difflib
R=Path(__file__).resolve().parent;A=R/(R/'latest-claude-a.txt').read_text()
card=json.loads((A/'card.json').read_text(encoding='utf-8'))
assert card.get('conclusion'),'A did not produce a diagnosis'
W=R/'claude-b'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');W.mkdir(parents=True)
ws=Path.home()/('day26-order-repair-'+W.name)
shutil.copytree(R/'blind-baseline',ws,ignore=shutil.ignore_patterns('bin','obj'))
(ws/'diagnosis-card.json').write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
(W/'workspace.txt').write_text(str(ws),encoding='utf-8')
conf={'mcpServers':{'repair':{'command':'python','args':[str(R/'repair_mcp.py')],'env':{'REPAIR_ROOT':str(ws),'REPAIR_AUDIT':str(W/'tool-audit.jsonl'),'PYTHONUTF8':'1'}}}}
(W/'mcp.json').write_text(json.dumps(conf),encoding='utf-8')
prompt='''這是新的修復工作階段。請先讀diagnosis-card.json、specs/requirements.md與必要原始碼，再真正做最小修改，最後呼叫build。
僅可用工具修改教學C#副本，不能更改測試或規格。保留500ms客戶背景查詢及其先完成再取消的順序，不得刪除或縮短；保留取消、退款旗標、授權、冪等及通知契約與客服稽核用途。不可調高ThreadPool最小/最大值當修法，不要把阻塞包進Task.Run。
工具只有read_file、replace_text、build。replace_text需一段唯一且完全相同舊文字。固定建置工具不做runtime或負載驗證。
最後用繁體中文說明真正改動、為何、代價，以及仍未驗證或需決策的部分。不要宣稱已通過負載測試。'''
(W/'prompt.txt').write_text(prompt,encoding='utf-8')
args=['claude','-p','--model','sonnet','--tools','','--allowedTools','mcp__repair__read_file,mcp__repair__replace_text,mcp__repair__build','--strict-mcp-config','--mcp-config',str(W/'mcp.json'),'--setting-sources','project','--settings',json.dumps({'disableAllHooks':True,'autoMemoryEnabled':False}),'--no-session-persistence','--output-format','stream-json','--verbose']
t=time.time()
with (W/'trace.jsonl').open('w',encoding='utf-8') as out,(W/'stderr.txt').open('w',encoding='utf-8') as err:
 p=subprocess.run(args,input=prompt,cwd=ws,stdout=out,stderr=err,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},timeout=600)
res={}
for l in (W/'trace.jsonl').read_text(encoding='utf-8').splitlines():
 try:
  x=json.loads(l)
  if x.get('type')=='result':res=x
 except ValueError:pass
(W/'answer.md').write_text(res.get('result',''),encoding='utf-8')
patch=[]
for rel in ['src/Api/Program.cs','src/Domain/Cancellation.cs']:
 a=(R/'blind-baseline'/rel).read_text(encoding='utf-8').splitlines(True);b=(ws/rel).read_text(encoding='utf-8').splitlines(True)
 patch.extend(difflib.unified_diff(a,b,fromfile='before/'+rel,tofile='after/'+rel))
(W/'diff.patch').write_text(''.join(patch),encoding='utf-8')
(W/'execution.json').write_text(json.dumps({'exit':p.returncode,'seconds':round(time.time()-t,1),'cost_usd':res.get('total_cost_usd'),'turns':res.get('num_turns'),'subtype':res.get('subtype')},indent=2),encoding='utf-8')
(R/'latest-claude-b.txt').write_text(str(W.relative_to(R)),encoding='utf-8')
print('DONE',W,p.returncode,res.get('total_cost_usd'),res.get('num_turns'))
