from pathlib import Path
import argparse,subprocess,sys,json,time,datetime
r=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('name');a=ap.parse_args()
if not a.name.replace('-','').replace('_','').isalnum():ap.error('simple new name required')
out=r/'runs'/a.name;out.mkdir(parents=True,exist_ok=False);steps=[];start=time.monotonic()
for name,cmd in [('routing-selftest',[sys.executable,'route-review.py','--selftest']),('domain',['dotnet','run','--project','tests/DomainTests']),('integration',[sys.executable,'verify-integration.py',a.name+'-integration'])]:
 p=subprocess.run(cmd,cwd=r,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
 (out/(name+'.txt')).write_text(p.stdout+p.stderr,encoding='utf-8');steps.append({'step':name,'command':cmd,'exit':p.returncode})
 if p.returncode:break
report={'steps':steps,'pass':len(steps)==3 and all(s['exit']==0 for s in steps),'elapsed_seconds':time.monotonic()-start,'human_minutes':None,'remote_ci':False,'business_accepted':False}
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report));raise SystemExit(0 if report['pass'] else 1)
