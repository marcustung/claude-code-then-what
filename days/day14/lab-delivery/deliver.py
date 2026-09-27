"""Check, package and verify a candidate locally. Never deploys or grants approval."""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib,os
r=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('version',choices=['baseline','fixed','release-next']);ap.add_argument('name');ap.add_argument('--with-concurrency',action='store_true');ap.add_argument('--diagnose-with-claude',action='store_true',help='transmit limited teaching failure evidence to Claude; explicit opt-in');a=ap.parse_args()
if a.diagnose_with_claude and a.version!='baseline':ap.error('current transmission scope permits baseline teaching files only')
if not a.name.replace('-','').replace('_','').isalnum():ap.error('simple new name required')
o=r/'runs'/a.name;o.mkdir(exist_ok=False);src=r/a.version;steps=[];package=o/'package'
env=os.environ.copy();env.pop('OC_TEST_DELAY_MS',None);env.pop('OC_FAULTS',None)
commands=[('ci',[sys.executable,'ci.py',a.name+'-ci']),('publish',['dotnet','publish','src/Api/Api.csproj','-c','Release','-o',str(package),'--nologo']),('smoke',[sys.executable,'verify-integration.py',a.name+'-smoke','--artifact',str(package)])]
if a.with_concurrency:commands.insert(1,('concurrency',[sys.executable,str(r/'verify.py'),a.version,a.name+'-concurrency']))
try:
 for name,cmd in commands:
  try:
   c=subprocess.run(cmd,cwd=src,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
   (o/(name+'.txt')).write_text(c.stdout+c.stderr,encoding='utf-8');steps.append(dict(step=name,exit=c.returncode))
  except subprocess.TimeoutExpired:steps.append(dict(step=name,exit=None,error='timeout'));break
  if c.returncode:break
  if name=='publish':
   manifest={str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in package.rglob('*') if p.is_file()}
   (o/'package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
finally:
 report=dict(steps=steps,passed=len(steps)==len(commands) and all(s['exit']==0 for s in steps),remote_deployed=False,owner_accepted=False)
 (o/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# A diagnosis is saved beside the failed run. It never changes delivery acceptance.
if not report['passed'] and a.diagnose_with_claude:
 from diagnose_failure import diagnose
 report['diagnosis']=diagnose(r,src,o,report)
 (o/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report));raise SystemExit(0 if report['passed'] else 1)
