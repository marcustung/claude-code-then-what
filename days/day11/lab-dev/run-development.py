from pathlib import Path
import subprocess,json,hashlib,datetime,time,shutil,difflib,sys
root=Path(__file__).resolve().parent

def files():
 return {str(p.relative_to(root)).replace('\\','/'):p.read_bytes() for name in ['src','tests','specs','design-input'] for p in (root/name).rglob('*') if p.is_file() and not set(p.parts)&{'bin','obj'}} | {n:(root/n).read_bytes() for n in ['CLAUDE.md','plan.md']}
def main():
 for stage,allowed in [('tests','tests/DomainTests/Program.cs'),('impl','src/Domain/Cancellation.cs')]:
  out=root/'runs'/stage;out.mkdir(exist_ok=False);before=files();start=time.monotonic()
  args=[shutil.which('claude.exe') or shutil.which('claude'),'-p','--model','sonnet','--effort','medium','--setting-sources','project','--tools','Read,Grep,Glob,Edit,Write','--allowedTools','Read,Grep,Glob,Edit,Write','--no-session-persistence','--output-format','stream-json','--verbose']
  prompt=(root/'prompts'/f'{stage}.txt').read_text(encoding='utf-8');(out/'prompt.txt').write_text(prompt,encoding='utf-8')
  with (out/'trace.jsonl').open('w',encoding='utf-8') as o,(out/'stderr.txt').open('w',encoding='utf-8') as e:
   p=subprocess.run(args,input=prompt,text=True,encoding='utf-8',cwd=root,stdout=o,stderr=e,timeout=600)
  after=files();changed=[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)]
  meta={'stage':stage,'args':args,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'changed':changed,'allowed_file':allowed,'scope_ok':set(changed)=={allowed},'inputs_before':{k:hashlib.sha256(v).hexdigest() for k,v in before.items()},'inputs_after':{k:hashlib.sha256(v).hexdigest() for k,v in after.items()},'human_minutes':None,'actor':'automated Claude Code execution, not human worklog'}
  for line in (out/'trace.jsonl').read_text(encoding='utf-8').splitlines():
   try:x=json.loads(line)
   except ValueError:continue
   if x.get('type')=='result':
    (out/'result.md').write_text(x.get('result',''),encoding='utf-8');meta['model_result']={k:v for k,v in x.items() if k!='result'}
  (out/'diff.patch').write_text(''.join(''.join(difflib.unified_diff(before.get(k,b'').decode('utf-8').splitlines(True),after.get(k,b'').decode('utf-8').splitlines(True),fromfile='a/'+k,tofile='b/'+k)) for k in changed),encoding='utf-8')
  snap=out/'snapshot'
  for k,v in after.items():
   q=snap/k;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(v)
  if p.returncode or not meta['scope_ok'] or meta.get('model_result',{}).get('is_error',True):
   (out/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');raise RuntimeError('model or scope failed '+stage)
  t=subprocess.run(['dotnet','run','--project','tests/DomainTests'],cwd=root,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=120)
  (out/'tests.txt').write_text(t.stdout+t.stderr,encoding='utf-8');meta['test_exit']=t.returncode;meta['test_command']='dotnet run --project tests/DomainTests';meta['tests_executed_by']='outer runner'
  (out/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
  print(stage,'model',p.returncode,'scope',meta['scope_ok'],'test exit',t.returncode,flush=True)
  if stage=='tests' and not (t.returncode==1 and 'FAIL SC-03' in t.stdout):raise RuntimeError('unexpected red test')
  if stage=='impl' and t.returncode!=0:raise RuntimeError('green failed')
if __name__=='__main__': main()
