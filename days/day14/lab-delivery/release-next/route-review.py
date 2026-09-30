from pathlib import Path
import json,re,sys
root=Path(__file__).resolve().parent
policy=json.loads((root/'routing-policy.json').read_text())
def route(diff):
 paths=re.findall(r'^\+\+\+ b/(.+)$',diff,re.M)
 hits=[p for p in paths if any(p.startswith(prefix) for prefix in policy['owner_paths'])]
 return {'route':'OWNER_REQUIRED' if hits or not paths else 'AI_REVIEW','paths':paths,'owner_hits':hits,'accepted':False,'reason':'core path' if hits else 'unknown diff' if not paths else 'requires evidence review'}
if '--selftest' in sys.argv:
 assert route('+++ b/src/Domain/Cancellation.cs')['route']=='OWNER_REQUIRED'
 assert route('+++ b/docs/readme.md')['route']=='AI_REVIEW'
 assert route('')['route']=='OWNER_REQUIRED'
 print('3 routing checks passed; no human approval inferred')
else: print(json.dumps(route((root/'diff.patch').read_text(encoding='utf-8')),indent=2))
