"""Two read-only tools: Grafana queries and an exact allowlist of teaching files."""
import sys,os,json,subprocess
from pathlib import Path
base=Path(os.environ['LAB_SOURCE_ROOT']).resolve()
# Reuse the gcx adapter implementation, without its stdin loop.
source=Path(os.environ['LAB_GCX_ADAPTER']).read_text(encoding='utf-8-sig').split('for line in sys.stdin:')[0]
ns={};exec(source,ns)
ns['SCHEMA']['properties']['operation']['enum'].append('metrics_range')
allowed=['src/Api/Program.cs','src/Domain/Cancellation.cs','specs/requirements.md','evidence/client-summary.json','evidence/stacks.txt']
for line in sys.stdin:
 q={}
 try:
  q=json.loads(line);ident=q.get('id');method=q.get('method')
  if ident is None:continue
  if method=='initialize':result={'protocolVersion':q['params']['protocolVersion'],'capabilities':{'tools':{}},'serverInfo':{'name':'order-investigation-readonly','version':'1'}}
  elif method=='tools/list':result={'tools':[
   {'name':'query_observability','description':'Read teaching incident Grafana using gcx. No writes.', 'inputSchema':ns['SCHEMA']},
   {'name':'read_project','description':'Read an explicitly provided source/spec/evidence file with line numbers. Stacks are a separate diagnostic capture of the same deployed source, not the timed load run.', 'inputSchema':{'type':'object','properties':{'path':{'type':'string','enum':allowed},'start_line':{'type':'integer','minimum':1},'max_lines':{'type':'integer','minimum':1,'maximum':120}},'required':['path']}}]}
  elif method=='tools/call':
   name=q['params']['name'];a=q['params']['arguments']
   if name=='query_observability':
    if a['operation']=='metrics_range':
     from datetime import datetime
     span=(datetime.fromisoformat(a['end'].replace('Z','+00:00'))-datetime.fromisoformat(a['start'].replace('Z','+00:00'))).total_seconds()
     if not 0<span<=120:raise ValueError('range must be 0..120 seconds')
     args=['gcx','metrics','query','-d','prometheus',a['expression'],'--from',a['start'],'--to',a['end'],'--step','1s','-o','json']
     p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=40)
     entry={'argv':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
     with open(os.environ['DAY24_TOOL_AUDIT'],'a',encoding='utf-8') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
     result={'content':[{'type':'text','text':json.dumps(entry,ensure_ascii=False)}],'isError':p.returncode!=0}
    else:result=ns['execute'](a)
   elif name=='read_project':
    path=a['path']
    if path not in allowed:raise ValueError('path not allowed')
    p=(base/path).resolve()
    if not p.is_relative_to(base):raise ValueError('outside root')
    lines=p.read_text(encoding='utf-8-sig').splitlines(); start=max(1,int(a.get('start_line',1))); limit=max(1,min(120,int(a.get('max_lines',100)))); text=f'Total lines: {len(lines)}. Showing {start}..{min(start+limit-1,len(lines))}.\n'+'\n'.join(f'{i}: {x}' for i,x in enumerate(lines,1) if start<=i<start+limit)
    result={'content':[{'type':'text','text':text}]}
    with open(os.environ['DAY24_TOOL_AUDIT'],'a',encoding='utf-8') as f:f.write(json.dumps({'tool':name,'path':path,'start_line':start,'max_lines':limit,'line_count':len(text.splitlines())})+'\n')
   else:raise ValueError('tool not allowed')
  else:result={}
  print(json.dumps({'jsonrpc':'2.0','id':ident,'result':result},ensure_ascii=False),flush=True)
 except Exception as e:print(json.dumps({'jsonrpc':'2.0','id':q.get('id'),'error':{'code':-32603,'message':str(e)}}),flush=True)
