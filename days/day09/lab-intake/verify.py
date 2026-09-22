from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent;m=json.loads((r/'runs/interview-01/meta.json').read_text(encoding='utf-8'))
unchanged=all(hashlib.sha256((r/k).read_bytes()).hexdigest()==v for k,v in m['inputs'].items())
skill=False
for l in (r/'runs/interview-01/trace.jsonl').read_text(encoding='utf-8').splitlines():
 try:e=json.loads(l)
 except ValueError:continue
 for c in e.get('message',{}).get('content',[]) if isinstance(e.get('message',{}).get('content'),list) else []:
  if isinstance(c,dict) and c.get('name')=='Skill' and c.get('input',{}).get('skill')=='intake-interview:grilling':skill=True
api=(r/'src/Api/Program.cs').read_text(encoding='utf-8');q=json.loads((r/'runs/codegraph-01/03-stdout.txt').read_text(encoding='utf-8'))
missing=not any(c.get('filePath')=='src/Api/Program.cs' for c in q['callers'])
result={'inputs_unchanged':unchanged,'actual_skill_call':skill,'api_call_in_source':'Cancellation.Cancel(before)' in api,'api_missing_from_saved_callers':missing,'human_answers':m['human_answers']}
print(json.dumps(result,indent=2));assert unchanged and skill and result['api_call_in_source'] and missing
