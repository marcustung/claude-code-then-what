from pathlib import Path
import argparse, subprocess, json, shutil, sys, hashlib, os
R=Path(__file__).resolve().parent

def policy(review, approval, revision, domain):
    if review.get('revision')!=revision or review.get('status')!='completed':return 'review'
    if review.get('important',0):return 'review'
    if domain and not (approval.get('revision')==revision and approval.get('role')=='domain-owner' and approval.get('accepted') is True):return 'owner'
    return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('name');a=ap.parse_args()
    if not a.name.replace('-','').replace('_','').isalnum():ap.error('new simple run name required')
    out=R/'runs'/a.name;out.mkdir(exist_ok=False)
    specs=[('01','build-error','build'),('02','rule-error','domain'),('03','api-error','integration'),('04','review-unavailable','review'),('05','owner-missing','owner'),('06','broken-package','smoke'),('07','ordinary-change',None),('08','domain-approved',None),('09','review-nit',None),('10','rule-repaired',None)]
    (out/'expectations.json').write_text(json.dumps(specs,indent=2),encoding='utf-8')
    results=[]
    for id,name,expected in specs:
        case=out/id;src=case/'source';shutil.copytree(R/'fixed',src,ignore=shutil.ignore_patterns('bin','obj','runs','__pycache__'));(src/'runs').mkdir()
        domainfile=src/'src/Domain/Cancellation.cs';api=src/'src/Api/Program.cs'
        original=domainfile.read_text(encoding='utf-8')
        if id=='01':domainfile.write_text(original+'\nINVALID CSHARP !\n',encoding='utf-8')
        if id=='02':domainfile.write_text(original.replace('order.Paid && !order.Cancelled','order.Paid'),encoding='utf-8')
        if id=='03':
            t=api.read_text(encoding='utf-8');assert 'statusCode: 401' in t;api.write_text(t.replace('statusCode: 401','statusCode: 400'),encoding='utf-8')
        if id=='10':
            # Recreate the same faulty input as case 02, then restore before the independent rerun.
            (case/'before.cs').write_text(original.replace('order.Paid && !order.Cancelled','order.Paid'),encoding='utf-8')
            (case/'repair.json').write_text(json.dumps({'repair':'restore no-repeat-refund guard','previous_case':'02'}),encoding='utf-8')
        revision=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((src/'src').rglob('*.cs')))).hexdigest()
        review={'fixture':True,'revision':revision,'status':'unavailable' if id=='04' else 'completed','important':0,'nits':1 if id=='09' else 0}
        approval={'fixture':True,'revision':revision,'role':'domain-owner','accepted':id!='05'}
        (case/'policy-input.json').write_text(json.dumps({'review':review,'approval':approval,'domain_change':id not in ['07','09']},indent=2),encoding='utf-8')
        steps=[];blocked=None
        def run(stage,cmd):
            try:
                p=subprocess.run(cmd,cwd=src,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
                (case/(stage+'.txt')).write_text(p.stdout+p.stderr,encoding='utf-8');rc=p.returncode
            except subprocess.TimeoutExpired:rc=124
            steps.append({'stage':stage,'exit':rc});return rc==0
        checks=[('build',['dotnet','build','src/Api/Api.csproj','--nologo']),('domain',['dotnet','run','--project','tests/DomainTests']),('integration',[sys.executable,'verify-integration.py','integration'])]
        for stage,cmd in checks:
            if not run(stage,cmd):blocked=stage;break
        if not blocked:blocked=policy(review,approval,revision,id not in ['07','09'])
        package=case/'package'
        if not blocked:
            if not run('publish',['dotnet','publish','src/Api/Api.csproj','-c','Release','-o',str(package),'--nologo']):blocked='publish'
            else:
                manifest={str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in package.rglob('*') if p.is_file()}
                (case/'package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
                if id=='06':(package/'Api.runtimeconfig.json').write_text('{ invalid json',encoding='utf-8')
                if not run('smoke',[sys.executable,'verify-integration.py','smoke','--artifact',str(package)]):blocked='smoke'
        eligible=blocked is None
        if eligible:(case/'ready-for-load.json').write_text(json.dumps({'package':str(package),'revision':revision,'scope':'local fixture acceptance; not remote approval'}),encoding='utf-8')
        result={'id':id,'scenario':name,'expected_block':expected,'actual_block':blocked,'matches':blocked==expected,'steps':steps,'package_created':package.exists(),'ready_for_load':eligible,'policy_inputs':'synthetic fixtures, no real reviewer or model invocation'}
        results.append(result);(case/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
    summary={'scope':'local executable checks plus synthetic review/approval fixtures; not remote CI or merge protection','cases':results,'matched':sum(x['matches'] for x in results),'blocked':sum(x['actual_block'] is not None for x in results),'ready':sum(x['ready_for_load'] for x in results)}
    (out/'report.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return 0 if summary['matched']==10 else 1
if __name__=='__main__':sys.exit(main())
