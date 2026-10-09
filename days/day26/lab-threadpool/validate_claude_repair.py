from pathlib import Path
import json, argparse, subprocess
R=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--workspace');opts=parser.parse_args()
B=R/(R/'latest-claude-b.txt').read_text().strip()
ws=Path(opts.workspace).resolve() if opts.workspace else Path((B/'workspace.txt').read_text().strip())
if opts.workspace:
 for project in ['Api','FakeSink']:
  subprocess.run(['dotnet','build',str(ws/'src'/project/(project+'.csproj')),'-c','Release','--nologo'],check=True)

s=(R/'run.py').read_text(encoding='utf-8').split('summaries=[]')[0]
s=s.replace("RUN=R/'runs'/", "RUN=R/'repair-validation'/")
anchor='  lat=[r[\'latency_ms\'] for r in rows]'
extra='''  # Additional regression declared before this run: 16 callers cancel the SAME order.
  req(ab,'/orders',{'id':'race-order','paid':True})
  with ThreadPoolExecutor(max_workers=16) as racepool:
   race=list(racepool.map(lambda _:req(ab,'/orders/race-order/cancel',{}),range(16)))
  time.sleep(1)
  race_receipts=[json.loads(l) for l in (d/'sink/receipts.jsonl').read_text().splitlines() if json.loads(l)['order_id']=='race-order']
  race_result={'responses':race,'transitions':sum(body.get('transitioned') is True for status,body in race),'receipts':len(race_receipts),'unique_notification_ids':len({x['notification_id'] for x in race_receipts})}
  (d/'same-order.json').write_text(json.dumps(race_result,indent=2),encoding='utf-8')
  checks['same_order_only_one_transition']=race_result['transitions']==1
  checks['same_order_only_one_notification']=race_result['receipts']==1
'''
assert anchor in s;s=s.replace(anchor,extra+anchor)
ns={'__file__':str(R/'run.py')};exec(s,ns)
ns['API']=ws/'src/Api/bin/Release/net9.0/Api.dll'
if opts.workspace: ns['SINK']=ws/'src/FakeSink/bin/Release/net9.0/FakeSink.dll'
results=[ns['one']('claude-repair',i) for i in range(2)]
(ns['RUN']/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
(ns['RUN']/'source-repair.txt').write_text(str(B),encoding='utf-8')
(ns['RUN']/'source-workspace.txt').write_text(str(ws),encoding='utf-8')
(R/'latest-validation.txt').write_text(str(ns['RUN'].relative_to(R)),encoding='utf-8')
print('DONE',ns['RUN'])
