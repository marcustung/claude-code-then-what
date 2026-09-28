from pathlib import Path
import json,hashlib,urllib.request,shutil,subprocess,time
base=Path(r'<HOME>\day15-k6-planner-20260928')
root=Path(r'<REPO>')
lab=root/'examples/sdlc-delivery/day15-lab'
work=base/'workspace';work.mkdir()
records=base/'records';records.mkdir()
sha='99e22125a780dae3cbf74c2e1a130b1062a61305'
url=f'https://raw.githubusercontent.com/grafana/xk6-subcommand-agent/{sha}/agents/skills/k6-test-planner/SKILL.md'
data=urllib.request.urlopen(url).read()
p=work/'plugin/skills/k6-test-planner/SKILL.md';p.parent.mkdir(parents=True);p.write_bytes(data)
meta=work/'plugin/.claude-plugin/plugin.json';meta.parent.mkdir();meta.write_text(json.dumps({'name':'day15-official-planner','version':'0.0.1','description':'Pinned official k6-test-planner; experiment-local wrapper'}))
shutil.copy2(lab/'performance-test-plan.md',records/'original-plan.md')
shutil.copy2(lab/'load.js',records/'original-load.js')
inputs=json.loads((lab/'claude-input.json').read_text(encoding='utf-8-sig'))
# Only the two source files, not the original prompt, plan or prior conclusions.
def collect(o):
 if isinstance(o,dict):
  for k,v in o.items():
   if k in ['src/Api/Program.cs','src/Domain/Cancellation.cs'] and isinstance(v,str):
    dest=work/k;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(v,encoding='utf-8')
   elif isinstance(v,(dict,list)):collect(v)
 elif isinstance(o,list):
  for x in o:collect(x)
collect(inputs)
assert (work/'src/Api/Program.cs').exists()
brief='''# Independent planning inputs
Teaching order cancellation API. Read both C# files to discover endpoints and architecture.
Requirements: shipped orders cannot be cancelled; paid unshipped orders request refund once (flag only, no actual payment); repeated cancellation must not add notifications; each transition should have one receiver receipt.
Environment: Windows loopback, .NET9, k6 1.3.0 CLI available to external runner; no production traffic, no company SLA. Target is the existing unchanged packaged service. No service code edits permitted in this experiment.
Predeclared teaching criteria: first cancellation p95<250ms, HTTP failure rate 0 for expected-success workloads, all behavior checks pass, no dropped iterations. These are NOT production promises. Suggested additional bounds must be labeled hypotheses for confirmation.
Budget: recommend ONE highest-value additional local experiment, <=60 seconds load, <=10 new orders/sec, <=50 VUs, <=20sec post-load drain. Need expected observations, evidence and stop rules before execution. Longer soak is outside this run.
No MCP available. Tools limited to Read/Grep/Glob/Skill. Do not claim MCP/version/doc queries executed. Planner research step not available; state limitation.
'''
(work/'brief.md').write_text(brief,encoding='utf-8')
(base/'empty-mcp.json').write_text('{"mcpServers":{}}')
prompt='''Invoke the day15-official-planner:k6-test-planner skill using the Skill tool first. Read brief.md and the two C# sources. Independently formulate a performance test strategy in Traditional Chinese. No prior test plans or results are available to you. Explain missing inputs, goals, risks, prioritized test matrix, ONE concrete bounded experiment recommendation, acceptance criteria and stop conditions. Do not execute or modify anything. Explicitly state unavailable MCP research. Do not invent SLA, facts or test results. Return markdown, not scripts.'''
(records/'prompt.txt').write_text(prompt,encoding='utf-8')
manifest={'skill_commit':sha,'skill_url':url,'skill_sha256':hashlib.sha256(data).hexdigest(),'mode':'local plugin wrapper, explicit Skill tool; no MCP; independent planning not full official end-to-end workflow','inputs':{str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob('*') if p.is_file()},'original_plan_sha256':hashlib.sha256((records/'original-plan.md').read_bytes()).hexdigest()}
(records/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
args=[str(Path.home()/'.local/bin/claude.exe'),'-p',prompt,'--model','sonnet','--effort','medium','--restricted','--tools','Read,Grep,Glob,Skill','--allowedTools','Read,Grep,Glob,Skill','--setting-sources','','--strict-mcp-config','--mcp-config',str(base/'empty-mcp.json'),'--plugin-dir',str(work/'plugin'),'--output-format','stream-json','--verbose','--no-session-persistence','--max-budget-usd','3']
(records/'command.json').write_text(json.dumps(args,ensure_ascii=False,indent=2),encoding='utf-8')
t=time.monotonic()
with (records/'trace.jsonl').open('w',encoding='utf-8') as out,(records/'stderr.txt').open('w',encoding='utf-8') as err:
 try:r=subprocess.run(args,cwd=work,stdout=out,stderr=err,timeout=240);rc=r.returncode
 except subprocess.TimeoutExpired:rc=124
meta={'exit_code':rc,'elapsed_seconds':round(time.monotonic()-t,2)}
(records/'execution.json').write_text(json.dumps(meta))
print(json.dumps(meta))
for line in (records/'trace.jsonl').read_text(encoding='utf-8').splitlines():
 try:
  e=json.loads(line)
  if e.get('type')=='result':
   (records/'result.json').write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8')
   (records/'strategy.md').write_text(e.get('result',''),encoding='utf-8')
   print(e.get('result','')[:16000])
 except json.JSONDecodeError:pass