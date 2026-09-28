from pathlib import Path
import argparse,json,collections,math
ap=argparse.ArgumentParser();ap.add_argument('run');a=ap.parse_args()
if not a.run.replace('-','').replace('_','').isalnum():ap.error('simple run name required')
r=Path(__file__).resolve().parent/'runs'/a.run
groups=collections.defaultdict(list)
for line in (r/'k6-samples.json').open(encoding='utf-8'):
 x=json.loads(line)
 if x.get('type')=='Point' and x.get('metric')=='cancel_ms':groups[x['data']['tags']['stage']].append(x['data']['value'])
def percentile(xs,p):
 v=sorted(xs);i=(len(v)-1)*p;lo=int(i);hi=math.ceil(i);return v[lo]+(v[hi]-v[lo])*(i-lo)
stages=[{'stage':k,'samples':len(groups[k]),'p95_ms':round(percentile(groups[k],.95),3),'max_ms':round(max(groups[k]),3)} for k in ['0-1','1-5','5-10','10-0'] if groups[k]]
resources=collections.defaultdict(list)
for row in json.loads((r/'metrics-samples.json').read_text()):
 for line in row.get('metrics','').splitlines():
  parts=line.split()
  if len(parts)==2 and parts[0] in ['oc_working_set_bytes','oc_gc_heap_bytes','oc_notify_queue_depth','oc_gc_collections_gen2']:resources[parts[0]].append(float(parts[1]))
v={'stages':stages,'resource_observations':{k:{'min':min(xs),'max':max(xs),'first':xs[0],'last':xs[-1]} for k,xs in resources.items()},'limits':'stage tag at cancellation completion; .5s resource sampling can miss peaks; no CPU or server-side distributed tracing'}
print(json.dumps(v,indent=2))
