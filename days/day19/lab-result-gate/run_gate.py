"""Single post-analysis entry: exit code controls dispatch, no side effects."""
from pathlib import Path
import subprocess,sys,json,datetime,hashlib
root=Path(__file__).resolve().parent
if len(sys.argv)!=4: raise SystemExit("Usage: python run_gate.py RESULT TASK EVIDENCE")
inputs=[Path(x).resolve() for x in sys.argv[1:]]
out=root/"runs"/("gate-"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"));out.mkdir(parents=True)
p=subprocess.run([sys.executable,str(root/"check_result.py"),*[str(x) for x in inputs]],capture_output=True,text=True,encoding="utf-8")
try:check=json.loads(p.stdout)
except ValueError:check={"state":"CHECKER_ERROR","errors":[p.stderr],"approved":False}
record={"input_hashes":{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs},"check":check,"checker_exit":p.returncode,"next_queue":("needs-followup" if check.get("state")=="NEEDS_FOLLOWUP" else "human-review") if p.returncode==0 else None,"external_dispatch":False}
(out/"result.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(record,ensure_ascii=False,indent=2));print("Saved:",out)
sys.exit(p.returncode)
