
from pathlib import Path
import subprocess,json,os,time
lab=Path(__file__).resolve().parent;run=Path((lab/"latest-run.txt").read_text());w=run/"claude"
if (w/"trace.jsonl").exists():raise RuntimeError("Existing model evidence: choose a new run; never overwrite.")
w.mkdir(exist_ok=True)
import shutil,sys
shutil.copytree(lab/"after/src",w/"src",ignore=shutil.ignore_patterns("bin","obj"),dirs_exist_ok=True)
shutil.copy2(lab.parent/"order-cancel-lifecycle/specs/notification-contract-v2.1.md",w/"notification-contract.md")
(w/"CLAUDE.md").write_text("Read only synthetic files in this directory. Do not access parent, home or company files.")
cfg={"mcpServers":{"observability":{"command":sys.executable,"args":[str(lab/"gcx_readonly_mcp.py")],"env":{"GCX_CONFIG":(lab/"gcx-config-location.txt").read_text(),"DAY24_TOOL_AUDIT":str(w/"tool-audit.jsonl"),"PYTHONUTF8":"1"}}}}
(w/"mcp.json").write_text(json.dumps(cfg))
prompt="Read only src and notification-contract.md. Use query_observability to investigate why cancellation API is fast but notifications arrive later. Discover sources, query both receiver logs, select one slow notification and retrieve its actual trace; compare with code. Test missing-receiver-demo once and distinguish query failure from non-delivery. Before has no central export; empty results are unknown, not proof of no execution. Service names day24-api-normal/day24-fakesink-normal/day24-api-slow/day24-fakesink-slow. Max14 queries. Explain observations/inference/unknown in Traditional Chinese. Run windows: "+json.dumps([{k:r[k] for k in ["variant","case","start","end"]} for r in json.loads((run/"summary.json").read_text())])
(w/"prompt.txt").write_text(prompt,encoding="utf8")
args=["claude","-p",(w/"prompt.txt").read_text(encoding="utf8"),"--model","sonnet","--effort","medium","--restricted","--tools","Read,Grep,Glob","--allowedTools","Read,Grep,Glob,mcp__observability__query_observability","--setting-sources","project","--settings",json.dumps({"disableAllHooks":True,"autoMemoryEnabled":False}),"--strict-mcp-config","--mcp-config",str(w/"mcp.json"),"--output-format","stream-json","--verbose","--no-session-persistence","--max-budget-usd","3"]
start=time.time()
with (w/"trace.jsonl").open("w",encoding="utf8") as out,(w/"stderr.txt").open("w",encoding="utf8") as err:
 p=subprocess.run(args,cwd=w,stdout=out,stderr=err,timeout=300)
(w/"execution.json").write_text(json.dumps({"exit_code":p.returncode,"elapsed_seconds":round(time.time()-start,2),"model":"sonnet","tools":"Read,Grep,Glob + readonly gcx adapter","budget_usd":3},indent=2))
print("Claude exit",p.returncode)
