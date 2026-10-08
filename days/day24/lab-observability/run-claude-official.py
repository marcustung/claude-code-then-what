"""Comparison run: same question and data as run-claude.py, but Claude runs gcx directly via Bash
with the official debug-with-grafana Skill (gcx's intended agent usage) instead of the custom MCP adapter.
Read-only is enforced by a Bash allowlist of gcx query subcommands plus the Viewer token."""
from pathlib import Path
import subprocess,json,os,time,shutil,sys
lab=Path(__file__).resolve().parent;run=lab/Path((lab/"latest-run.txt").read_text().strip());import sys as _s
OUT=_s.argv[1] if len(_s.argv)>1 else "claude-official-skill"
w=run/OUT
if (w/"trace.jsonl").exists():raise RuntimeError("Existing model evidence: choose a new run; never overwrite.")
w.mkdir(exist_ok=True)
shutil.copytree(lab/"after/src",w/"src",ignore=shutil.ignore_patterns("bin","obj"),dirs_exist_ok=True)
shutil.copy2(lab.parent/"order-cancel-lifecycle/specs/notification-contract-v2.1.md",w/"notification-contract.md")
skill=Path.home()/".claude/skills/debug-with-grafana"
# --restricted ignores project/user skills; ship the Skill as a plugin via --plugin-dir
plug=w/"_plugin"
shutil.copytree(skill,plug/"skills/debug-with-grafana",dirs_exist_ok=True)
(plug/".claude-plugin").mkdir(parents=True,exist_ok=True)
(plug/".claude-plugin/plugin.json").write_text(json.dumps({"name":"gcx-debug","version":"0.1.0","description":"debug-with-grafana Skill from gcx"}))
(w/"CLAUDE.md").write_text("Only synthetic teaching materials in this directory. Read only. Use gcx via Bash to retrieve telemetry (query subcommands only). Do not read parent/home/company files. Distinguish observations, inference, unknown. No changes.")
base=(run/"claude/prompt.txt").read_text(encoding="utf8")
prompt=base.replace("請自行透過提供的 query_observability 工具探索來源","請自行透過 Bash 執行 gcx 探索來源（本機 context 已設定好；可使用 debug-with-grafana Skill）")
assert prompt!=base
(w/"prompt.txt").write_text(prompt,encoding="utf8")
allow=["Read","Grep","Glob","Skill"]+[f"Bash(gcx {c}:*)" for c in ["datasources list","logs query","logs labels","logs series","metrics query","metrics labels","traces query","traces get","traces labels"]]
env=dict(os.environ,GCX_CONFIG=os.path.join(os.environ["TEMP"],"day24-gcx-private.yaml"),PYTHONUTF8="1")
args=["claude","-p",prompt,"--model","sonnet","--effort","medium","--restricted","--tools","Read,Grep,Glob,Bash,Skill","--allowedTools",",".join(allow),"--setting-sources","project","--settings",json.dumps({"disableAllHooks":True,"autoMemoryEnabled":False}),"--strict-mcp-config","--output-format","stream-json","--verbose","--no-session-persistence","--max-budget-usd","3","--plugin-dir",str(plug)]
start=time.time()
with (w/"trace.jsonl").open("w",encoding="utf8") as out,(w/"stderr.txt").open("w",encoding="utf8") as err:
 p=subprocess.run(args,cwd=w,stdout=out,stderr=err,env=env,timeout=900)
(w/"execution.json").write_text(json.dumps({"exit_code":p.returncode,"elapsed_seconds":round(time.time()-start,2),"model":"sonnet","tools":"Read,Grep,Glob,Skill + Bash allowlist of gcx query subcommands","skill":"debug-with-grafana","allowed":allow,"budget_usd":3},indent=2))
print("Claude exit",p.returncode)
