from pathlib import Path
import hashlib,json,itertools
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
files=[]
for name,meta in manifest.items():
 actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
 files.append({'file':name,'unchanged':actual==meta['sha256']})
rows=[]
for shipped,cancelled,paid in itertools.product([False,True],repeat=3):
 guard=False if shipped or cancelled else paid
 expression=not shipped and not cancelled and paid
 naive=False if shipped else paid
 rows.append({'shipped':shipped,'cancelled':cancelled,'paid':paid,'guard':guard,'expression':expression,'naive':naive,'equivalent':guard==expression})
runs=[]
for folder in ['r1','r2','reader-01','reader-02']:
 events=[json.loads(line) for line in (root/'runs'/folder/'trace.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
 calls=[b for e in events if e.get('type')=='assistant' for b in e.get('message',{}).get('content',[]) if b.get('type')=='tool_use']
 result=next(e for e in events if e.get('type')=='result')
 runs.append({'run':folder,'tool_names':sorted(set(c['name'] for c in calls)),'tool_calls':len(calls),'allowed_only':all(c['name'] in ['Read','Grep','Glob'] for c in calls),'model_ids':sorted(set(e.get('message',{}).get('model') for e in events if e.get('message',{}).get('model'))),'completed':not result.get('is_error',True)})
report={'input_hashes':files,'predicate_rows':rows,'runs':runs,'limits':'Predicate illustration only; not execution of .NET, not semantic verification of model report, not business approval.'}
print(json.dumps(report,ensure_ascii=False,indent=2))
assert all(f['unchanged'] for f in files)
assert all(row['equivalent'] for row in rows)
assert sum(row['naive']!=row['expression'] for row in rows)==1
assert all(x['allowed_only'] and x['completed'] for x in runs)
