"""Exercise the real CLI; expectations are fixed in cases.json."""
from pathlib import Path
import subprocess,sys,json,datetime,hashlib
root=Path(__file__).resolve().parent
out=root/"runs"/datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f");out.mkdir(parents=True)
rows=[]
for case in json.loads((root/"cases.json").read_text(encoding="utf-8")):
    args=[sys.executable,str(root/"check_result.py"),str(root/"fixtures"/case["file"]),str(root/"task.json"),str(root/"evidence.json")]
    p=subprocess.run(args,capture_output=True,text=True,encoding="utf-8")
    got=json.loads(p.stdout)
    ok=p.returncode==case["exit"] and got["state"]==case["state"] and all(e in got["errors"] for e in case["errors"])
    rows.append({**case,"actual_exit":p.returncode,"actual":got,"matches_expected":ok})
    (out/(case["name"]+".json")).write_text(json.dumps(got,ensure_ascii=False,indent=2),encoding="utf-8")
report={"type":"deterministic teaching fixtures, not model evaluation", "rows":rows,"all_expected":all(x["matches_expected"] for x in rows),"input_hashes":{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/"check_result.py",root/"cases.json",root/"task.json",root/"evidence.json",*sorted((root/"fixtures").glob("*.json"))]}}
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"output":str(out),"cases":len(rows),"matched":sum(x["matches_expected"] for x in rows)},ensure_ascii=False))
sys.exit(0 if report["all_expected"] else 1)
