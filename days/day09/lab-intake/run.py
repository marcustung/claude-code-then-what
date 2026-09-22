from pathlib import Path
import subprocess,shutil,json,hashlib,sys
r=Path(__file__).resolve().parent
name=sys.argv[1] if len(sys.argv)>1 else 'interview-01'
if not name.replace('-','').replace('_','').isalnum():raise ValueError('simple run name required')
o=r/'runs'/name;o.mkdir(parents=True,exist_ok=False)
inputs={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['src','tests','interview-plugin'] for p in (r/base).rglob('*') if p.is_file()}
inputs['spec.md']=hashlib.sha256((r/'spec.md').read_bytes()).hexdigest()
args=[shutil.which('claude.exe') or str(Path.home()/'.local/bin/claude.exe'),'-p','--model','sonnet','--effort','medium','--setting-sources','project','--plugin-dir',str(r/'interview-plugin'),'--tools','Read,Grep,Glob,Skill','--allowedTools','Read,Grep,Glob,Skill','--no-session-persistence','--output-format','stream-json','--verbose']
prompt=(r/'prompt.txt').read_text(encoding='utf-8');(o/'prompt.txt').write_text(prompt,encoding='utf-8')
with (o/'trace.jsonl').open('w',encoding='utf-8') as f,(o/'stderr.txt').open('w',encoding='utf-8') as e:
 p=subprocess.run(args,input=prompt,text=True,encoding='utf-8',stdout=f,stderr=e,cwd=r,timeout=600)
meta={'args':args,'exit_code':p.returncode,'inputs':inputs,'inputs_unchanged':all(hashlib.sha256((r/k).read_bytes()).hexdigest()==v for k,v in inputs.items()),'human_answers':0}
for l in (o/'trace.jsonl').read_text(encoding='utf-8').splitlines():
 try:x=json.loads(l)
 except ValueError:continue
 if x.get('type')=='result':
  (o/'result.md').write_text(x.get('result',''),encoding='utf-8');meta['result']={k:v for k,v in x.items() if k!='result'}
(o/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print('saved',o,'exit',p.returncode,'unchanged',meta['inputs_unchanged'])
