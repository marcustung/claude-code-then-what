"""Day12: fresh verifier sessions and one bounded repair in an isolated fixture.
Uses authenticated Claude Code; consumes model usage. No production or git changes.
"""
from pathlib import Path
import argparse,shutil,subprocess,json,time,hashlib,difflib
ROOT=Path(__file__).resolve().parent
AGENT="""You are an integration verifier. Read CLAUDE.md, plan.md and specs/rules-v2.md.
Execute the exact local verification commands in the task. Read generated reports and raw payloads.
Compare behavior against the supplied rules. Report commands, observed failures, code locations, and untested scope.
Do not edit source, tests, rules or runner. Running tests may create build products and run records.
Do not assume a failed command is a product bug; distinguish build/environment failures.
Report only; never repair. Never contact production or external payment services.
"""

def main():
 ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('--model',default='sonnet');a=ap.parse_args()
 if not a.name.replace('-','').replace('_','').isalnum():ap.error('simple unused run name required')
 cli=shutil.which('claude.exe') or shutil.which('claude')
 if not cli:raise RuntimeError('Install and authenticate Claude Code first')
 out=ROOT/'runs'/a.name;out.mkdir(exist_ok=False);work=out/'workspace';work.mkdir()
 for d in ['src','tests','specs']:shutil.copytree(ROOT/d,work/d,ignore=shutil.ignore_patterns('bin','obj'))
 for f in ['VERSION','verify-integration.py']:shutil.copy2(ROOT/f,work/f)
 (work/'runs').mkdir()
 (work/'CLAUDE.md').write_text("""# Day12 integration demonstration
Read plan.md and specs/rules-v2.md. RefundRequested is a request flag, not a payment.
This NEW fixture allows verification commands; the earlier Domain-only demonstration restrictions do not apply.
Verification: dotnet run --project tests/DomainTests (seven PASS); python verify-integration.py <unused-name> (11 checks, pass true).
Verifier must not edit source/tests/spec/runner. Repair may edit ONLY src/Api/Program.cs.
No new dependencies, real payments, network services beyond the loopback fixture, or altered acceptance criteria.
Stop on environmental failure or need for new business decisions. Tool output is evidence, self-report is not.
""",encoding='utf-8')
 (work/'plan.md').write_text('Verify paid/unpaid/shipped cancellation and sequential repeat through API. Domain computes refund flag; API response and notification must forward the same result. Diagnose failures; change no test or rule. Scope: local sequential integration, not concurrency or real authorization.',encoding='utf-8')
 (out/'agents.json').write_text(json.dumps({'order-verifier':{'description':'Run local order integration checks and report evidence, never repair','prompt':AGENT,'tools':['Read','Grep','Glob','Bash']}}),encoding='utf-8')
 (out/'mcp.json').write_text('{"mcpServers":{}}')
 api=work/'src/Api/Program.cs';original=api.read_text(encoding='utf-8');old='"order_cancelled", result.RefundRequested);'
 assert original.count(old)==1
 api.write_text(original.replace(old,'"order_cancelled", false);'),encoding='utf-8')
 def hashes():
  return {f.relative_to(work).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in work.rglob('*') if f.is_file() and not {'bin','obj','runs','.claude'}.intersection(f.relative_to(work).parts)}
 initial=hashes();report={'model':a.model,'mutation':'notification flag forced false by host, not a model error','stages':[],'human_minutes':None,'status':'STARTED'}
 def save(): (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 def call(stage,prompt,verifier):
  rd=out/stage;rd.mkdir();(rd/'prompt.txt').write_text(prompt,encoding='utf-8');before=hashes()
  allowed=['Read','Grep','Glob','Bash(python verify-integration.py *)','Bash(dotnet run --project tests/DomainTests)'] if verifier else ['Read','Grep','Glob','Edit']
  args=[cli,'-p','--model',a.model,'--effort','medium','--setting-sources','project','--strict-mcp-config','--mcp-config',str((out/'mcp.json').resolve()),'--tools','Read,Grep,Glob,Bash' if verifier else 'Read,Grep,Glob,Edit','--allowedTools',*allowed,'--no-session-persistence','--output-format','stream-json','--verbose']
  if verifier:args+=['--agents',str((out/'agents.json').resolve()),'--agent','order-verifier']
  start=time.monotonic()
  with (rd/'trace.jsonl').open('w',encoding='utf-8') as o,(rd/'stderr.txt').open('w',encoding='utf-8') as e:
   proc=subprocess.run(args,input=prompt,cwd=work,text=True,encoding='utf-8',stdout=o,stderr=e,timeout=420)
  events=[]
  for line in (rd/'trace.jsonl').read_text(encoding='utf-8').splitlines():
   try:events.append(json.loads(line))
   except ValueError:pass
  result=next((e for e in reversed(events) if e.get('type')=='result'),{})
  (rd/'result.md').write_text(result.get('result',''),encoding='utf-8')
  after=hashes();changed=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]
  item={'stage':stage,'exit':proc.returncode,'elapsed_seconds':round(time.monotonic()-start,2),'turns':result.get('num_turns'),'cost_usd':result.get('total_cost_usd'),'changed':changed,'result_error':result.get('is_error'),'permission_denials':result.get('permission_denials',[])}
  report['stages'].append(item);save();print(json.dumps(item),flush=True)
  assert proc.returncode==0 and result and not result.get('is_error'),stage+' model failure'
  assert not changed if verifier else set(changed)<= {'src/Api/Program.cs'},stage+' unexpected source changes'
  return result.get('result','')
 try:
  diagnosis=call('verify-red','Run dotnet run --project tests/DomainTests and python verify-integration.py verifier-red. These commands are permitted. Read runs/verifier-red/report.json and its requests.json, payloads.json, logs.jsonl. Explain whether the change meets plan.md, where any inconsistency originates, and which fields the notification check does not cover. Do not change any source or tests. Reply in Traditional Chinese.',True)
  red=json.loads((work/'runs/verifier-red/report.json').read_text(encoding='utf-8'));failed=[c['name'] for c in red['checks'] if not c['pass']]
  assert failed==['notification-ids-and-flags'],'Unexpected red baseline'
  mutated=api.read_text(encoding='utf-8')
  call('repair','Read CLAUDE.md, plan.md, specs/rules-v2.md and runs/verifier-red/report.json with raw payloads. Repair ONLY src/Api/Program.cs to satisfy the established forwarding behavior. Do not change tests, Domain, runner, specs or permissions. You have Edit but no execution tools; a fresh verifier will execute after you. If a new requirement is needed, report it and stop. Prior independent verifier report: '+diagnosis,False)
  (out/'repair.diff').write_text(''.join(difflib.unified_diff(mutated.splitlines(True),api.read_text(encoding='utf-8').splitlines(True),fromfile='before/Program.cs',tofile='after/Program.cs')),encoding='utf-8')
  call('verify-green','Independently verify current code against plan.md and specs/rules-v2.md. Run dotnet run --project tests/DomainTests and python verify-integration.py verifier-green. Read the generated report and raw requests, payloads, logs. Report the outcome and untested scope. Do not modify source or tests. Do not rely on old runs. Reply in Traditional Chinese.',True)
  green=json.loads((work/'runs/verifier-green/report.json').read_text(encoding='utf-8'))
  final=hashes();report.update({'failed_checks_before':failed,'green_checks':len(green['checks']),'green_pass':green['pass'],'protected_unchanged':all(final.get(k)==v for k,v in initial.items() if k!='src/Api/Program.cs'),'status':'VERIFIED' if green['pass'] else 'NOT_FIXED'})
  assert report['protected_unchanged'] and green['pass']
 except Exception as e:
  report['status']='STOPPED';report['error']=str(e);save();raise
 save();print(json.dumps({'status':report['status']}));return 0
if __name__=='__main__':raise SystemExit(main())
