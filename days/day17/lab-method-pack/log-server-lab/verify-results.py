"""Verify saved MCP evidence, not the model's self-reported success."""
from pathlib import Path
import argparse,json,re,hashlib
L=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('--attempt',default='r2');a=ap.parse_args()
o=L/'runs'/a.name
checks=[];rows=[]
def check(case,name,ok,detail=None):checks.append({'case':case,'check':name,'passed':bool(ok),'detail':detail})
def texts(result):
 c=result.get('content','')
 return c if isinstance(c,str) else '\n'.join(x.get('text','') for x in c if isinstance(x,dict))
for case in ['complete','missing-receipts','query-failure']:
 d=o/'model'/a.attempt/case;w=o/'workspaces'/case
 calls=json.loads((d/'tool-calls.json').read_text(encoding='utf-8'));responses=json.loads((d/'tool-results.json').read_text(encoding='utf-8'))
 task=json.loads((w/'task.json').read_text(encoding='utf-8'));truth=json.loads((o/'audit'/(case+'.json')).read_text(encoding='utf-8'))
 execution=json.loads((d/'execution.json').read_text(encoding='utf-8'));byid={x['tool_use_id']:x for x in responses}
 answer=(d/'answer.md').read_text(encoding='utf-8');found=re.findall(r'```json\s*(\{.*?\})\s*```',answer,re.S)
 value=json.loads(found[-1]) if found else {}
 check(case,'model_completed',execution['exit']==0)
 skill=[c for c in calls if c['name']=='Skill']
 check(case,'skill_loaded_successfully',any('Launching skill: day17-trace:trace-notification' in texts(byid.get(c['id'],{})) and not byid.get(c['id'],{}).get('is_error') for c in skill))
 queries=[c for c in calls if c['name']=='mcp__grafana__query_loki_logs']
 check(case,'mcp_log_query_called',len(queries)>0,len(queries))
 scoped=all(c['input'].get('datasourceUid')==task['datasource_uid'] and case in c['input'].get('logql','') and c['input'].get('startRfc3339')==task['time_start'] and c['input'].get('endRfc3339')==task['time_end'] for c in queries)
 check(case,'query_scope_matches_task',scoped)
 allowed={'Glob','Grep','Read','Skill','mcp__grafana__list_datasources','mcp__grafana__get_datasource','mcp__grafana__query_loki_logs','mcp__grafana__list_loki_label_names','mcp__grafana__list_loki_label_values','mcp__grafana__query_loki_stats'}
 check(case,'read_only_tools_only',all(c['name'] in allowed for c in calls))
 before=json.loads((d/'input-manifest.json').read_text(encoding='utf-8'))
 after={str(f.relative_to(w)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in w.rglob('*') if f.is_file()}
 check(case,'workspace_unchanged',before==after)
 expected='confirmed' if case=='complete' else 'unknown'
 check(case,'receiver_status',value.get('receiver_status')==expected,value.get('receiver_status'))
 check(case,'sender_status',value.get('sender_status')==('unknown' if case=='query-failure' else 'confirmed'),value.get('sender_status'))
 check(case,'output_contract',all(k in value for k in ['order_id','sender_status','receiver_status','missing_sources','next_action']) and value.get('order_id')==task['order_id'] and isinstance(value.get('missing_sources'),list) and bool(value.get('next_action')))
 parsed=[]
 for c in queries:
  reply=byid.get(c['id'],{})
  try:body=json.loads(texts(reply))
  except ValueError:body={}
  parsed.append((c,reply,body))
 nid=truth['receiver_ground_truth'][0]['notification_id']
 if case!='query-failure':
  receiver=[(c,r,b) for c,r,b in parsed if nid in c['input']['logql'] and 'notification-receiver' in c['input']['logql']]
  check(case,'independent_receiver_query_by_notification_id',bool(receiver))
  check(case,'receiver_query_success',bool(receiver) and all(not r.get('is_error') and isinstance(b.get('data'),list) for c,r,b in receiver))
  if case=='complete':
   entries=[json.loads(item['line']) for c,r,b in receiver for item in b.get('data',[]) if 'line' in item]
   check(case,'actual_receiver_evidence_matches_id',any(e.get('event')=='notification_received' and e.get('notification_id')==nid and e.get('order_id')==task['order_id'] for e in entries))
  else:
   check(case,'successful_empty_result_not_delivery_failure',bool(receiver) and all(b.get('data')==[] for c,r,b in receiver) and value.get('receiver_status')=='unknown')
 else:
  check(case,'actual_backend_error_not_empty_result',any(r.get('is_error') and '502' in texts(r) for c,r,b in parsed))
  check(case,'no_successful_log_response',not any(isinstance(b.get('data'),list) for c,r,b in parsed))
  check(case,'failure_retained_in_output','502' in answer and bool(value.get('missing_sources')))
 rows.append({'case':case,'receiver_status':value.get('receiver_status'),'sender_status':value.get('sender_status'),'log_queries':len(queries),'cost_usd':execution.get('cost_usd'),'turns':execution.get('turns')})
report={'run':a.name,'attempt':a.attempt,'passed':all(x['passed'] for x in checks),'passed_checks':sum(x['passed'] for x in checks),'total_checks':len(checks),'cases':rows,'checks':checks,'limits':['program checks do not validate every semantic sentence','one run per case per version','no production or team savings claim']}
(o/('verification-'+a.attempt+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
for c in checks:
 if not c['passed']:print('FAILED '+json.dumps(c,ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)