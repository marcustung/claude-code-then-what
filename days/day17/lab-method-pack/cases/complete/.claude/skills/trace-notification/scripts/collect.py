from pathlib import Path
import json,sys

def collect(root):
 root=Path(root); task=json.loads((root/'task.json').read_text(encoding='utf-8-sig')); order=task['order_id']
 out={'order_id':order,'expected_version':task['version'],'sources':{},'missing_sources':[],'errors':[],'events':[],'receipts':[]}
 for name in ['logs.jsonl','receipts.json']:
  p=root/'data'/name
  if not p.exists():
   out['sources'][name]='missing';out['missing_sources'].append(name);continue
  try:
   raw=p.read_text(encoding='utf-8-sig'); rows=[json.loads(x) for x in raw.splitlines() if x.strip()] if name.endswith('jsonl') else json.loads(raw)
   if not isinstance(rows,list) or any(not isinstance(x,dict) for x in rows):raise ValueError('expected object records')
   out['sources'][name]='present'
   if name=='logs.jsonl':
    ids={x.get('notification_id') for x in rows if x.get('order_id')==order and x.get('notification_id')}
    for n,x in enumerate(rows,1):
     if x.get('order_id')==order or x.get('notification_id') in ids:out['events'].append({'source':f'data/{name}:{n}','record':x})
   else:
    for n,x in enumerate(rows):
     if x.get('payload',{}).get('order_id')==order:out['receipts'].append({'source':f'data/{name} item {n}','record':x})
  except (ValueError,TypeError) as e:
   out['sources'][name]='invalid';out['errors'].append({'source':name,'error':str(e)})
 return out
if __name__=='__main__':
 root=Path(sys.argv[1]);result=collect(root);(root/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'sources':result['sources'],'events':len(result['events']),'receipts':len(result['receipts'])}));sys.exit(2 if result['errors'] else 0)
