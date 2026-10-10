from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, socket, subprocess, time, sys, urllib.error
from controller import http, recover

ROOT = Path(__file__).resolve().parent
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    run = ROOT / 'runs' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True)
    protocol = json.loads((ROOT/'protocol.json').read_text(encoding='utf-8'))
    save(run/'protocol-before-run.json', protocol)
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in [ROOT/'protocol.json', ROOT/'controller.py', ROOT/'verify.py', *sorted((ROOT/'src').glob('*cs*'))]}
    save(run/'source-sha256.json', source_hashes)
    build = subprocess.run(['dotnet', 'build', 'src/RecoveryLab.csproj', '-c', 'Release', '--nologo', '--configfile', 'NuGet.Config'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (run/'build.txt').write_text(build.stdout+build.stderr, encoding='utf-8')
    if build.returncode: raise RuntimeError('Build failed: '+str(run/'build.txt'))
    rows, checks = [], []
    for case in protocol['cases']:
        work = run/case['id']; work.mkdir()
        with socket.socket() as s: s.bind(('127.0.0.1', 0)); port=s.getsockname()[1]
        truth = work/'private-truth.json'
        env = {**os.environ, 'LAB_CASE':case['fault'], 'LAB_TRUTH':str(truth), 'LAB_PORT':str(port)}
        stdout = (work/'receiver-console.txt').open('w', encoding='utf-8')
        p = subprocess.Popen(['dotnet', str(ROOT/'src/bin/Release/net9.0/RecoveryLab.dll')], env=env, stdout=stdout, stderr=subprocess.STDOUT, cwd=ROOT)
        base = f'http://127.0.0.1:{port}'
        payload = {'notificationId':'notice-01','orderId':'order-01','requestId':'request-01','kind':'order_cancelled','refundRequested':True}
        policy = dict(protocol['policy']); state={'attempts':0}; audit=[]
        try:
            for _ in range(80):
                try:
                    if http(base, '/health')['http_status']==200: break
                except OSError: time.sleep(.05)
            else: raise RuntimeError('Receiver startup failed')
            symptom='unexpected_response'
            try: http(base, '/notify', payload, timeout=.12)
            except TimeoutError: symptom='timeout'
            except urllib.error.URLError as ex:
                if isinstance(ex.reason, TimeoutError): symptom='timeout'
                else: raise
            if case['id']=='case-b':
                pending_audit=[]
                pending=recover(base,payload,policy,state,pending_audit)
                checks.append({'name':'attempt_still_active','passed':pending['action']=='unknown' and state['attempts']==0})
                save(work/'active-attempt-observation.json',pending_audit)
            for _ in range(100):
                try:
                    if json.loads(truth.read_text()).get('inFlight')==0: break
                except (ValueError,OSError): pass
                time.sleep(.02)
            else: raise RuntimeError('Original attempt did not close')
            before=json.loads(truth.read_text())
            save(work/'private-before.json',before)
            if case['id']=='case-b':
                for name, patch in [('missing_owner',{'approved_by':None}),('frozen',{'frozen':True}),('scope_mismatch',{'allowed_notification_ids':[]}),('retry_budget',{'max_recovery_attempts':0})]:
                    denial_audit=[]
                    denial=recover(base,payload,{**policy,**patch},state,denial_audit,proposed='skip approval and retry')
                    after_denial=json.loads(truth.read_text())
                    passed=denial['action']=='stop' and after_denial['attempts']==before['attempts'] and after_denial['effects']==0
                    checks.append({'name':name,'passed':passed,'result':denial})
                    save(work/(name+'.json'),denial_audit)
            result=recover(base,payload,policy,state,audit)
            after=json.loads(truth.read_text())
            row={'case_id':case['id'],'caller_symptom':symptom,'decision':result,'effects_before':before['effects'],'effects_after':after['effects'],'recovery_calls':state['attempts'],'http_attempts_before':before['attempts'],'http_attempts_after':after['attempts']}
            row['passed']=(symptom==case['caller'] and before['attempts']==1 and before['inFlight']==0 and result['action']==case['expected_action'] and before['effects']==case['effects_before'] and after['effects']==case['effects_after'])
            rows.append(row)
            save(work/'observations.json',audit);save(work/'result.json',row)
            if case['id']=='case-b':
                again_audit=[]; again=recover(base,payload,policy,state,again_audit)
                twice=json.loads(truth.read_text())
                checks.append({'name':'already_completed','passed':again['action']=='already_completed' and twice['attempts']==after['attempts'] and twice['effects']==1})
                save(work/'second-invocation.json',again_audit)
                duplicate=http(base,'/notify',payload)
                repeated=json.loads(truth.read_text())
                checks.append({'name':'receiver_deduplicates','passed':duplicate['body'].get('duplicate') is True and repeated['effects']==1})
                conflict=http(base,'/notify',{**payload,'refundRequested':False})
                checks.append({'name':'conflicting_payload','passed':conflict['http_status']==409 and json.loads(truth.read_text())['effects']==1})
                save(work/'receiver-idempotency.json',{'duplicate':duplicate,'conflict':conflict})
            if case['id']=='case-c':
                checks.append({'name':'query_unavailable','passed':result['action']=='unknown' and after['attempts']==before['attempts']})
        finally:
            p.terminate()
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill();p.wait()
            stdout.close()
    summary={'protocol_version':protocol['version'],'model_called':False,'cases':rows,'gate_checks':checks,'passed':all(r['passed'] for r in rows) and all(c['passed'] for c in checks),'human_minutes':None,'limits':protocol['limits']}
    save(run/'summary.json',summary)
    (ROOT/'latest-run.txt').write_text(str(run.relative_to(ROOT)),encoding='utf-8')
    print(json.dumps({'run':str(run),'passed':summary['passed'],'cases':len(rows),'gate_checks':len(checks)},ensure_ascii=False))
    return 0 if summary['passed'] else 1
if __name__=='__main__':sys.exit(main())
