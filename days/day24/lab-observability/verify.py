
"""Fetch raw telemetry, assert independent receipts and an actual async trace chain."""
from pathlib import Path
import json,subprocess,os,base64,hashlib
ROOT=Path(__file__).resolve().parent
run=Path((ROOT/"latest-run.txt").read_text());out=run/"recheck";out.mkdir(exist_ok=True)
env=os.environ.copy();env["GCX_CONFIG"]=(ROOT/"gcx-config-location.txt").read_text()
def query(name,args):
 p=subprocess.run(["gcx",*args,"-o","json"],capture_output=True,text=True,encoding="utf8",errors="replace",env=env)
 (out/(name+".json")).write_text(json.dumps({"argv":args,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr},indent=2))
 assert p.returncode==0,(name,p.stderr)
 return json.loads(p.stdout)
summary=json.loads((run/"summary.json").read_text())
assert len(summary)==4
for r in summary:
 assert r["cancellations"]==r["received"]==9 and r["duplicates"]==0 and not r["repeat_cancel_transitioned"]
 if r["variant"]!="after":continue
 result=query(r["case"]+"-receipts",["logs","query","-d","loki","--expr",'{service_name="day24-fakesink-'+r["case"]+'"} |= "notification_received"',"--from",r["start"],"--to",r["end"],"--limit","100"])
 # gcx returns backend-shaped or convenience JSON; match exact known independent IDs.
 original=[json.loads(x) for x in (run/("after-"+r["case"])/"receipts.jsonl").read_text().splitlines()]
 serialized=json.dumps(result)
 assert all(x["notification_id"] in serialized for x in original)
last=json.loads((run/"after-slow/receipts.jsonl").read_text().splitlines()[-1])
trace=query("trace",["traces","get","-d","tempo",last["trace_id"]])
# gcx wraps raw trace in {trace_id, trace}; preserve wrapper independently.
if "trace" in trace:trace=trace["trace"]
if isinstance(trace,str):trace=json.loads(trace)
spans=[s for b in trace.get("batches",trace.get("resourceSpans",[])) for scope in b["scopeSpans"] for s in scope["spans"]]
byname={s["name"]:s for s in spans}
api=byname["POST /orders/{id}/cancel"];worker=byname["notification.process"];client=byname["POST"];sink=byname["POST /notify"]
assert worker["parentSpanId"]==api["spanId"] and client["parentSpanId"]==worker["spanId"] and sink["parentSpanId"]==client["spanId"]
manifest=json.loads((ROOT/"source-manifest.json").read_text())
# 公開 repo 會統一換行、遮蔽註解裡的未來日次，原始 SHA-256 在那裡不會相同；
# 因此核對 before/ 與旁邊的原始版本子集逐檔一致（忽略換行差異），私人與公開兩邊都適用。
norm=lambda b:b.replace(b"\r\n",b"\n")
assert all(norm((ROOT/"before"/k.replace("\\","/")).read_bytes())==norm((ROOT.parent/"order-cancel-lifecycle"/k.replace("\\","/")).read_bytes()) for k in manifest)
assert (ROOT/"before/src/Domain/Cancellation.cs").read_bytes()==(ROOT/"after/src/Domain/Cancellation.cs").read_bytes()
(out/"result.json").write_text(json.dumps({"four_functional_runs":"PASS","18_receiver_ids_in_loki":"PASS","async_trace_parent_chain":"PASS","original_source_unchanged":"PASS"},indent=2))
print("PASS: four runs, 18 independent receiver IDs, async parent chain, original source.")
