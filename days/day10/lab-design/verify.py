from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((p/k).read_bytes()).hexdigest()==v['sha256'] for k,v in m.items())
e=[json.loads(l) for l in (p/'runs/design-01/trace.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
c=[b['name'] for x in e if x.get('type')=='assistant' for b in x.get('message',{}).get('content',[]) if b.get('type')=='tool_use']
assert c and set(c)<=set(['Read','Grep','Glob'])
a=[x for x in e if x.get('type')=='result'][-1]
assert not a.get('is_error',True)
print(json.dumps({'inputs':len(m),'hashes_match':True,'tool_calls':len(c),'tools':sorted(set(c)),'analysis_completed':True,'dotnet_executed':False}))
