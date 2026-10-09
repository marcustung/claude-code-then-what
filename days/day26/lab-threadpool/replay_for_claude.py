"""Publish only this teaching incident's runtime series/logs to the existing local LGTM."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,urllib.request
R=Path(__file__).resolve().parent
D=R/(R/'latest-blind.txt').read_text()
rows=[json.loads(x) for x in (D/'0-incident/api/runtime.jsonl').read_text().splitlines()]
logs=[json.loads(x) for x in (D/'0-incident/api/logs.jsonl').read_text().splitlines()]
ts=lambda s:datetime.fromisoformat(s.replace('Z','+00:00'))
shift=datetime.now(timezone.utc)-timedelta(seconds=10)-ts(rows[-1]['ts'])
ns=lambda s:str(int((ts(s)+shift).timestamp()*1e9))
attrs=lambda d:[{'key':k,'value':{'stringValue':str(v)}} for k,v in d.items()]
job='order-investigation-'+datetime.now(timezone.utc).strftime('%H%M%S')
resource={'attributes':attrs({'service.name':job,'deployment.environment':'teaching-replay'})}
def post(path,b):
 q=urllib.request.Request('http://127.0.0.1:4324'+path,json.dumps(b).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(q,timeout=30) as r:return r.status
keys={'threads':'oc_tp_threads','pending':'oc_tp_pending','completed':'oc_tp_completed','cpu_core_percent':'oc_cpu_core_percent','gc_heap_bytes':'oc_gc_heap_bytes'}
metrics=[{'name':v,'gauge':{'dataPoints':[{'asDouble':x[k],'timeUnixNano':ns(x['ts'])} for x in rows]}} for k,v in keys.items()]
post('/v1/metrics',{'resourceMetrics':[{'resource':resource,'scopeMetrics':[{'scope':{'name':'incident-replay'},'metrics':metrics}]}]})
for offset in range(0,len(logs),250):
 records=[{'timeUnixNano':ns(x['ts']),'severityText':x.get('level','INFO'),'body':{'stringValue':json.dumps(x)},'attributes':attrs({'original_ts':x['ts']})} for x in logs[offset:offset+250]]
 post('/v1/logs',{'resourceLogs':[{'resource':resource,'scopeLogs':[{'scope':{'name':'incident-replay'},'logRecords':records}]}]})
# Leave ample space for ingestion. Query end is the last shifted timestamp, not now.
win={'job':job,'start':(ts(rows[0]['ts'])+shift-timedelta(seconds=1)).isoformat(),'end':(ts(rows[-1]['ts'])+shift+timedelta(seconds=1)).isoformat(),'points':len(rows),'source_run':str(D.relative_to(R))}
(R/'replay-window-threadpool.json').write_text(json.dumps(win,indent=2),encoding='utf-8')
print(json.dumps(win))
