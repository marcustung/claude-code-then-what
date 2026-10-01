"""Prepare a local incident handoff; simulate elapsed time, never page people or replay orders."""
from pathlib import Path
import argparse,json
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--elapsed-seconds',type=int,default=0);ap.add_argument('--output',required=True);a=ap.parse_args()
for value in [a.run,a.output]:
 if not value.replace('-','').replace('_','').isalnum():ap.error('simple names required')
if a.elapsed_seconds<0:ap.error('nonnegative elapsed time required')
d=R/'runs'/a.run;incident=json.loads((d/'incident.json').read_text());report=json.loads((d/'report.json').read_text());receipts=json.loads((d/'receipts.json').read_text())
if not report['passed']:raise RuntimeError('rehearsal incomplete; do not claim service restored')
failed=[x for x in receipts if x['payload']['notification_id']==incident['notification_id']]
if len(failed)!=4 or any(x['status']!=503 for x in failed):raise RuntimeError('incident evidence mismatch')
policy={'primary_role':'service on-call (must assign a real person before team rollout)','escalation_role':'service owner (must assign a real person)','ack_deadline_seconds':300,'deadline_is':'teaching example, not company SLA','allowed':['read request/log/receipt evidence','verify deployed version and fresh probe'],'forbidden':['recreate missing order','replay notification','declare business reconciliation complete']}
card={'incident':incident,'policy':policy,'service':'restored in local rehearsal','business':'unresolved: original order lost on restart; no persisted notification replay source','state':'ESCALATE' if a.elapsed_seconds>=300 else 'WAITING_FOR_OWNER','elapsed_seconds':a.elapsed_seconds,'clock':'simulated argument, not a measured human response time','next_action':'assign service owner to reconcile the failed order and authorize any recovery','owner_acknowledged':False,'external_notification_sent':False,'automated_replay':False,'close_condition':'authorized owner verifies original business state and downstream outcome; not fulfilled here'}
o=R/'runs'/a.output;o.mkdir(exist_ok=False);(o/'handoff.json').write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(card,ensure_ascii=False))
