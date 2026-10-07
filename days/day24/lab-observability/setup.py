
"""Local demo only. Uses an isolated container; never removes containers or volumes."""
import subprocess,json,time,urllib.request,base64,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
IMAGE="grafana/otel-lgtm@sha256:d6b20e35890ef2f91d13944805939acdaf1e5d3ffbf9f9aed08586312826c815"
inspect=subprocess.run(["docker","inspect","day24-lgtm"],capture_output=True,text=True)
if inspect.returncode:
 subprocess.run(["docker","run","-d","--name","day24-lgtm","-p","127.0.0.1:3224:3000","-p","127.0.0.1:4324:4318","-p","127.0.0.1:9224:9090","-p","127.0.0.1:3324:3200",IMAGE],check=True)
else:
 info=json.loads(inspect.stdout)[0]
 for bindings in info["HostConfig"]["PortBindings"].values():
  assert all(b["HostIp"]=="127.0.0.1" for b in bindings),"Refuse non-loopback container"
 if not info["State"]["Running"]:subprocess.run(["docker","start","day24-lgtm"],check=True)
def api(path,data=None):
 req=urllib.request.Request("http://127.0.0.1:3224"+path,None if data is None else json.dumps(data).encode(),headers={"Authorization":"Basic "+base64.b64encode(b"admin:admin").decode(),"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)
for i in range(60):
 try:
  api("/api/health");break
 except Exception:time.sleep(1)
else:raise RuntimeError("Grafana not ready")
account=api("/api/serviceaccounts",{"name":"day24-reader-"+str(int(time.time())),"role":"Viewer"})
token=api(f'/api/serviceaccounts/{account["id"]}/tokens',{"name":"day24-lab","secondsToLive":86400})["key"]
conf=Path(os.environ.get("TEMP","."))/"day24-gcx-private.yaml"
r=subprocess.run(["gcx","login","day24","--config",str(conf),"--server","http://127.0.0.1:3224","--token",token,"--yes"],capture_output=True,text=True)
if r.returncode:raise RuntimeError("gcx login failed; private output withheld")
(ROOT/"gcx-config-location.txt").write_text(str(conf))
print("Ready: local Grafana :3224; Viewer token valid 24h; credentials outside sample.")
