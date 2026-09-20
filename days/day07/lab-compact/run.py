import shutil, os
from pathlib import Path
import subprocess,json,time,os
p=Path(__file__).resolve().parent
protocol=json.loads((p/'protocol.json').read_text())
cli = shutil.which('claude') or os.path.expanduser(r'~\.local\bin\claude.exe')
prompt=(p/'prompt.txt').read_text(encoding='utf-8')
args=[cli,'-p','--model',protocol['model'],'--effort','low','--safe-mode','--strict-mcp-config','--no-session-persistence','--output-format','stream-json','--verbose','--tools','Read','--allowedTools','Read']
for name in protocol['order']:
 d=p/name; d.mkdir()
 (d/'rule-card.md').write_bytes((p/(name.split('-')[0]+'.md')).read_bytes())
 start=time.time()
 try:
  r=subprocess.run(args,input=prompt,cwd=d,capture_output=True,text=True,encoding='utf-8',timeout=120)
  (d/'trace.jsonl').write_text(r.stdout,encoding='utf-8')
  (d/'stderr.txt').write_text(r.stderr,encoding='utf-8')
  (d/'meta.json').write_text(json.dumps({'exit_code':r.returncode,'started_unix':start,'wall_seconds':time.time()-start,'args':args},indent=2),encoding='utf-8')
  print(name,'exit',r.returncode,flush=True)
 except subprocess.TimeoutExpired as e:
  (d/'failure.txt').write_text(str(e),encoding='utf-8'); print(name,'TIMEOUT',flush=True); break
 if r.returncode: break
