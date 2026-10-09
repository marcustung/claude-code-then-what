"""Two read-only tools: Grafana queries and an exact allowlist of teaching files."""
import sys,os,json
from pathlib import Path
base=Path(os.environ['LAB_SOURCE_ROOT']).resolve()
# Reuse the gcx adapter implementation, without its stdin loop.
source=Path(os.environ['LAB_GCX_ADAPTER']).read_text(encoding='utf-8-sig').split('for line in sys.stdin:')[0]
ns={};exec(source,ns)
allowed=['src/Api/Program.cs','src/Domain/Cancellation.cs','specs/requirements.md','evidence/client-summary.json','evidence/stacks.txt']
for line in sys.stdin:
 q={}
 try:
  q=json.loads(line);ident=q.get('id');method=q.get('method')
  if ident is None:continue
  if method=='initialize':result={'protocolVersion':q['params']['protocolVersion'],'capabilities':{'tools':{}},'serverInfo':{'name':'order-investigation-readonly','version':'1'}}
  elif method=='tools/list':result={'tools':[
   {'name':'query_observability','description':'Read teaching incident Grafana using gcx. No writes.', 'inputSchema':ns['SCHEMA']},
   {'name':'read_project','description':'Read an explicitly provided source/spec/evidence file with line numbers. Stacks are a separate diagnostic capture of the same deployed source, not the timed load run.', 'inputSchema':{'type':'object','properties':{'path':{'type':'string','enum':allowed}},'required':['path']}}]}
  elif method=='tools/call':
   name=q['params']['name'];a=q['params']['arguments']
   if name=='query_observability':result=ns['execute'](a)
   elif name=='read_project':
    path=a['path']
    if path not in allowed:raise ValueError('path not allowed')
    p=(base/path).resolve()
    if not p.is_relative_to(base):raise ValueError('outside root')
    text='\n'.join(f'{i}: {x}' for i,x in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1))
    result={'content':[{'type':'text','text':text}]}
    with open(os.environ['DAY24_TOOL_AUDIT'],'a',encoding='utf-8') as f:f.write(json.dumps({'tool':name,'path':path,'line_count':len(text.splitlines())})+'\n')
   else:raise ValueError('tool not allowed')
  else:result={}
  print(json.dumps({'jsonrpc':'2.0','id':ident,'result':result},ensure_ascii=False),flush=True)
 except Exception as e:print(json.dumps({'jsonrpc':'2.0','id':q.get('id'),'error':{'code':-32603,'message':str(e)}}),flush=True)
