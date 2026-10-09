"""Bounded teaching-file edits and fixed dotnet build; no shell or arbitrary paths."""
import json,sys,os,subprocess,hashlib
from pathlib import Path
root=Path(os.environ['REPAIR_ROOT']).resolve();audit=Path(os.environ['REPAIR_AUDIT'])
readable=['src/Api/Program.cs','src/Domain/Cancellation.cs','specs/requirements.md','diagnosis-card.json']
editable=readable[:2]
def path(name,allowed):
 if name not in allowed:raise ValueError('file not allowed')
 p=(root/name).resolve()
 if not p.is_relative_to(root):raise ValueError('outside workspace')
 return p
schema=lambda props,required:{'type':'object','properties':props,'required':required,'additionalProperties':False}
for line in sys.stdin:
 q={}
 try:
  q=json.loads(line);ident=q.get('id')
  if ident is None:continue
  m=q.get('method')
  if m=='initialize':result={'protocolVersion':q['params']['protocolVersion'],'capabilities':{'tools':{}},'serverInfo':{'name':'bounded-teaching-repair','version':'1'}}
  elif m=='tools/list':result={'tools':[
   {'name':'read_file','description':'Read allowed teaching source/spec/diagnosis with line numbers.','inputSchema':schema({'path':{'type':'string','enum':readable}},['path'])},
   {'name':'replace_text','description':'Replace one unique exact source text occurrence in an allowed teaching C# file. Requires old text to match exactly once.','inputSchema':schema({'path':{'type':'string','enum':editable},'old':{'type':'string'},'new':{'type':'string'}},['path','old','new'])},
   {'name':'build','description':'Run fixed dotnet build src/Api/Api.csproj -c Release in teaching workspace. This does NOT run the service or load test.','inputSchema':schema({},[])}]}
  elif m=='tools/call':
   name=q['params']['name'];a=q['params'].get('arguments',{});entry={'tool':name,'arguments':a}
   if name=='read_file':
    p=path(a['path'],readable);out='\n'.join(f'{i}: {l}' for i,l in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1))
   elif name=='replace_text':
    p=path(a['path'],editable);s=p.read_text(encoding='utf-8-sig')
    if not a['old'] or s.count(a['old'])!=1:raise ValueError('old text must match exactly once')
    entry['before_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    p.write_text(s.replace(a['old'],a['new'],1),encoding='utf-8');entry['after_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();out='Source updated. Not yet built or runtime-tested.'
   elif name=='build':
    p=subprocess.run(['dotnet','build','src/Api/Api.csproj','-c','Release','--nologo'],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
    out=json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});entry['exit_code']=p.returncode
   else:raise ValueError('unknown tool')
   with audit.open('a',encoding='utf-8') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
   result={'content':[{'type':'text','text':out}]}
  else:result={}
  print(json.dumps({'jsonrpc':'2.0','id':ident,'result':result},ensure_ascii=False),flush=True)
 except Exception as e:print(json.dumps({'jsonrpc':'2.0','id':q.get('id'),'error':{'code':-32603,'message':str(e)}}),flush=True)
