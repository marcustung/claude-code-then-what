"""Join saved request and notification evidence; no model and no live actions."""
from pathlib import Path
import argparse,json
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('request_id');a=ap.parse_args()
r=Path(__file__).resolve().parent/'runs'/a.run
logs=[json.loads(x) for x in (r/'logs.jsonl').read_text(encoding='utf-8').splitlines()]
calls=json.loads((r/'requests.json').read_text(encoding='utf-8'));receipts=json.loads((r/'receipts.json').read_text(encoding='utf-8'))
matched=[x for x in calls if x['request_id']==a.request_id]
ids={x['response'].get('notification_id') for x in matched if x['response'].get('notification_id')}
ids.update(x['notification_id'] for x in logs if x.get('request_id')==a.request_id and x.get('notification_id'))
events=[x for x in logs if x.get('request_id')==a.request_id or x.get('notification_id') in ids]
result=dict(request=matched,events=events,receiver_attempts=[x for x in receipts if x['payload']['notification_id'] in ids],note='Empty results mean not found in this saved run, not proof that delivery never happened.')
print(json.dumps(result,ensure_ascii=False,indent=2))
