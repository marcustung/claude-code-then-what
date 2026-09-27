"""Validate saved Day14-17 teaching evidence. Does not run a model or deploy."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent
checks=[]
def read(run,file='report.json'):return json.loads((R/'runs'/run/file).read_text(encoding='utf-8'))
def check(name,v):checks.append({'name':name,'passed':bool(v)})
a=read('acceptance-auto-01');packet=read('acceptance-auto-01','diagnosis-input.json');model=read('acceptance-auto-01','diagnosis-result.json')
check('14 actual failure automatically diagnosed',not a['passed'] and a['diagnosis']['status']=='completed' and not model['is_error'] and bool(model['result']))
check('14 no package after failed check',not (R/'runs/acceptance-auto-01/package').exists() and [x['step'] for x in a['steps']]==['ci','concurrency'])
check('14 exact source allowlist',set(packet['sources'])=={'src/Api/Program.cs','src/Domain/Cancellation.cs'})
c=read('candidate-checked');check('14 good candidate passed four steps',c['passed'] and len(c['steps'])==4 and all(x['exit']==0 for x in c['steps']))
l=read('acceptance-load-02');k=read('acceptance-load-02','k6-summary.json');an=read('acceptance-load-02','analysis.json')
check('15 artifact and business checks',l['passed'] and all(l['checks'].values()) and l['before_sha256']==l['after_sha256'])
check('15 stage counts reconcile',sum(x['samples'] for x in an['stages'])==l['transitions']==1262 and k['metrics']['http_reqs']['count']==5048)
check('15 raw files present',all((R/'runs/acceptance-load-02'/x).exists() for x in ['receipts.json','logs.jsonl','k6-samples.json','metrics-samples.json']))
b=read('acceptance-rollback-01');check('16 actual update and rollback',b['passed'] and len(b['checks'])==18 and all(x['passed'] for x in b['checks']))
check('16 two distinct programs',hashlib.sha256((R/'runs/candidate-checked/package/Api.dll').read_bytes()).hexdigest()!=hashlib.sha256((R/'runs/acceptance-next-01/package/Api.dll').read_bytes()).hexdigest())
check('16 data loss explicit',any(x['name']=='rollback-does-not-restore-orders' and x['detail']==404 for x in b['checks']))
w=read('acceptance-handoff-wait','handoff.json');e=read('acceptance-handoff-escalate','handoff.json')
check('17 waiting and escalation simulated',w['state']=='WAITING_FOR_OWNER' and e['state']=='ESCALATE' and e['elapsed_seconds']==300)
check('17 no invented acceptance or replay',all(not x['owner_acknowledged'] and not x['external_notification_sent'] and not x['automated_replay'] for x in [w,e]))
check('17 same incident retained',w['incident']['notification_id']==e['incident']['notification_id']==read('acceptance-rollback-01','incident.json')['notification_id'])
result={'passed':all(x['passed'] for x in checks),'scope':'local teaching acceptance only; not production, team adoption, human response, or time savings','checks':checks}
print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['passed'] else 1)
