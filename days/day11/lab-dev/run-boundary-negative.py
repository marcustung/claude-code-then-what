"""Run an isolated notification-wiring negative control; preserve every run."""
from pathlib import Path
import argparse,shutil,subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('name');ns=ap.parse_args()
 if not ns.name.replace('-','').replace('_','').isalnum():ap.error('simple run name required')
 out=ROOT/'runs'/ns.name;out.mkdir(exist_ok=False)
 fixture=out/'fixture';fixture.mkdir()
 for folder in ['src','tests']:
  shutil.copytree(ROOT/folder,fixture/folder,ignore=shutil.ignore_patterns('bin','obj'))
 for f in ['verify-integration.py','VERSION']:
  shutil.copy2(ROOT/f,fixture/f)
 (fixture/'runs').mkdir()
 api=fixture/'src/Api/Program.cs';original=api.read_text(encoding='utf-8')
 old='"order_cancelled", result.RefundRequested);';new='"order_cancelled", false);'
 assert original.count(old)==1
 api.write_text(original.replace(old,new),encoding='utf-8')
 def run(label,args):
  r=subprocess.run(args,cwd=fixture,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
  (out/(label+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8');return r.returncode
 domain=run('domain-mutated',['dotnet','run','--project','tests/DomainTests'])
 red=run('integration-mutated',[sys.executable,'verify-integration.py','mutated'])
 api.write_text(original,encoding='utf-8')
 green=run('integration-restored',[sys.executable,'verify-integration.py','restored'])
 r=json.loads((fixture/'runs/mutated/report.json').read_text(encoding='utf-8'))
 g=json.loads((fixture/'runs/restored/report.json').read_text(encoding='utf-8'))
 failed=[x['name'] for x in r['checks'] if not x['pass']]
 result={'mutation':{'old':old,'new':new},'domain_exit':domain,'mutated_exit':red,'restored_exit':green,'failed_checks':failed,'restored_checks':len(g['checks']),'restored_pass':g['pass'],'domain_sha256':hashlib.sha256((fixture/'src/Domain/Cancellation.cs').read_bytes()).hexdigest(),'scope':'Isolated fixture; no model call; sequential loopback requests; no production claim.'}
 result['verified']=domain==0 and red!=0 and failed==['notification-ids-and-flags'] and green==0 and g['pass']
 (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result));return 0 if result['verified'] else 1
if __name__=='__main__':raise SystemExit(main())
