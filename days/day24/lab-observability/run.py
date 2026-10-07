
import os,sys,json,time,subprocess,socket,urllib.request,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
def now():return datetime.now(timezone.utc).isoformat()
def req(url,data=None):
 b=None if data is None else json.dumps(data).encode()
 r=urllib.request.Request(url,b,headers={"Content-Type":"application/json","X-Actor":"demo","X-Run-Id":CASE,"X-Request-Id":CASE+"-"+url.rsplit("/",2)[-2]})
 with urllib.request.urlopen(r,timeout=10) as f:return json.load(f)
def wait(url):
 for i in range(60):
  try:return req(url)
  except Exception:time.sleep(.5)
 raise RuntimeError(url+" not ready")
CASE=""
if __name__=="__main__":
 for port in [5124,5125]:
  s=socket.socket()
  try:s.bind(("127.0.0.1",port))
  finally:s.close()
 for v in ["before","after"]:
  for part in ["Api","FakeSink"]:
   subprocess.run(["dotnet","build",str(ROOT/v/"src"/part/(part+".csproj")),"--nologo","-v","quiet"],check=True)
 out=ROOT/"runs"/datetime.now().strftime("%Y%m%d-%H%M%S");out.mkdir(parents=True)
 (ROOT/"latest-run.txt").write_text(str(out))
 results=[]
 for v in ["before","after"]:
  for case,delay in [("normal",0),("slow",250)]:
   CASE=v+"-"+case;d=out/CASE;d.mkdir()
   env=os.environ.copy();env.update(OC_RUN_DIR=str(d),OC_SINK_URL="http://127.0.0.1:5125/notify",OC_SINK_DELAY_MS=str(delay),OC_FAULTS=str(d/"faults.json"),OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:4324",OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf",OTEL_METRIC_EXPORT_INTERVAL="1000",OTEL_BSP_SCHEDULE_DELAY="500",OTEL_BLRP_SCHEDULE_DELAY="500")
   (d/"faults.json").write_text("{}")
   processes=[];handles=[];start=now()
   try:
    for part,port in [("FakeSink",5125),("Api",5124)]:
     e=env.copy();e.update(ASPNETCORE_URLS=f"http://127.0.0.1:{port}",OTEL_SERVICE_NAME=f"day24-{part.lower()}-{case}")
     h=(d/(part+".console.log")).open("w");handles.append(h)
     processes.append(subprocess.Popen(["dotnet",str(ROOT/v/"src"/part/"bin/Debug/net9.0"/(part+".dll"))],env=e,stdout=h,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW))
     wait(f"http://127.0.0.1:{port}/health")
    requests=[]
    for i in range(9):
     oid=f"{CASE}-{i}"
     req("http://127.0.0.1:5124/orders",{"id":oid,"paid":False,"shipped":False})
     requests.append(req(f"http://127.0.0.1:5124/orders/{oid}/cancel",{}))
    duplicate=req(f"http://127.0.0.1:5124/orders/{CASE}-0/cancel",{})
    for i in range(100):
     receipts=req("http://127.0.0.1:5125/receipts")
     if receipts["received"]==9:break
     time.sleep(.1)
    time.sleep(8) # bounded exporter flush window
    metrics=urllib.request.urlopen("http://127.0.0.1:5124/metrics").read().decode()
    (d/"metrics.prom").write_text(metrics)
    result={"variant":v,"case":case,"start":start,"end":now(),"sink_delay_ms":delay,"cancellations":sum(x["transitioned"] for x in requests),"repeat_cancel_transitioned":duplicate["transitioned"],**receipts}
    (d/"requests.json").write_text(json.dumps(requests,indent=2))
    (d/"result.json").write_text(json.dumps(result,indent=2))
    assert result["cancellations"]==result["received"]==9 and result["duplicates"]==0 and not result["repeat_cancel_transitioned"],result
    results.append(result);print(json.dumps(result),flush=True)
   finally:
    for proc in processes:
     proc.terminate()
     try:proc.wait(5)
     except subprocess.TimeoutExpired:proc.kill();proc.wait()
    for h in handles:h.close()
 (out/"summary.json").write_text(json.dumps(results,indent=2))
 print("RUN="+str(out),flush=True)
