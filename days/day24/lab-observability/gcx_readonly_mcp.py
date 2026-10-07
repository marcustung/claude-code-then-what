
"""Read-only MCP adapter for gcx. No arbitrary shell, URL or config arguments."""
import sys,os,json,subprocess
SCHEMA={"type":"object","properties":{"operation":{"type":"string","enum":["datasources","logs","metrics","trace_search","trace_get"]},"datasource":{"type":"string","enum":["loki","prometheus","tempo","missing-receiver-demo"]},"expression":{"type":"string"},"start":{"type":"string"},"end":{"type":"string"},"trace_id":{"type":"string"}},"required":["operation"]}
def execute(a):
 op=a["operation"];ds=a.get("datasource",{"logs":"loki","metrics":"prometheus","trace_search":"tempo","trace_get":"tempo"}.get(op,""))
 if ds not in ["","loki","prometheus","tempo","missing-receiver-demo"]:raise ValueError("Unknown datasource")
 if op=="datasources":args=["datasources","list"]
 elif op=="logs":args=["logs","query","-d",ds,"--expr",a["expression"],"--limit","80"]
 elif op=="metrics":args=["metrics","query","-d",ds,a["expression"]]
 elif op=="trace_search":args=["traces","query","-d",ds,"--expr",a["expression"],"--limit","10"]
 elif op=="trace_get":
  tid=a["trace_id"]
  if len(tid)!=32 or any(x not in "0123456789abcdef" for x in tid):raise ValueError("Invalid trace ID")
  args=["traces","get","-d",ds,tid,"--llm"]
 else:raise ValueError("Unsupported operation")
 if op in ["logs","trace_search"]:
  args+=["--from",a["start"],"--to",a["end"]]
 if op=="metrics" and a.get("end"):args+=["--time",a["end"]]
 args+=["-o","json"]
 p=subprocess.run(["gcx",*args],capture_output=True,text=True,encoding="utf8",errors="replace",timeout=40)
 result={"argv":["gcx",*args],"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
 with open(os.environ["DAY24_TOOL_AUDIT"],"a",encoding="utf8") as f:f.write(json.dumps(result,ensure_ascii=False)+"\n")
 return {"content":[{"type":"text","text":json.dumps(result,ensure_ascii=False)}],"isError":p.returncode!=0}
for line in sys.stdin:
 try:
  q=json.loads(line);method=q.get("method");id=q.get("id")
  if id is None:continue
  if method=="initialize":result={"protocolVersion":q["params"]["protocolVersion"],"capabilities":{"tools":{}},"serverInfo":{"name":"day24-gcx-readonly","version":"1.0"}}
  elif method=="tools/list":result={"tools":[{"name":"query_observability","description":"Read synthetic Day24 local Grafana via gcx. Select datasource, query Logs/Metrics/Traces. Missing datasource is an error, never delivery evidence.","inputSchema":SCHEMA}]}
  elif method=="tools/call":result=execute(q["params"]["arguments"])
  elif method=="ping":result={}
  else:result={}
  print(json.dumps({"jsonrpc":"2.0","id":id,"result":result},ensure_ascii=False),flush=True)
 except Exception as e:
  print(json.dumps({"jsonrpc":"2.0","id":q.get("id"),"error":{"code":-32603,"message":str(e)}}),flush=True)
