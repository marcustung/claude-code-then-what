from pathlib import Path
import subprocess,json,threading,queue,time,argparse
L=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args()
out=L/'runs'/args.run
config=json.loads((out/'workspaces/complete/mcp.json').read_text(encoding='utf-8'))['mcpServers']['grafana']
p=subprocess.Popen([config['command'],*config['args']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
q=queue.Queue();errors=[]
def read():
 for line in p.stdout:
  try:q.put(json.loads(line))
  except ValueError:pass
def err():
 for line in p.stderr:errors.append(line)
threading.Thread(target=read,daemon=True).start();threading.Thread(target=err,daemon=True).start()
seq=0
history=[]
def rpc(method,params):
 global seq
 seq+=1
 msg={'jsonrpc':'2.0','id':seq,'method':method,'params':params}
 p.stdin.write(json.dumps(msg)+'\n');p.stdin.flush()
 until=time.monotonic()+30
 while time.monotonic()<until:
  r=q.get(timeout=30)
  if r.get('id')==seq:
   history.append({'request':msg,'response':r});return r
 raise RuntimeError('MCP timeout')
try:
 rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'day17-local-verifier','version':'1'}})
 p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
 result=rpc('tools/list',{})
 (out/'mcp-tools.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 for t in result['result']['tools']:
  if t['name']=='query_loki_logs':print(json.dumps(t,ensure_ascii=True))
 result=rpc('tools/call',{'name':'list_datasources','arguments':{}})
 print(json.dumps(result,ensure_ascii=True)[:1800])
finally:
 (out/'mcp-probe.json').write_text(json.dumps(history,ensure_ascii=False,indent=2),encoding='utf-8')
 p.stdin.close()
 try:p.wait(timeout=10)
 except subprocess.TimeoutExpired:p.terminate()
 (out/'mcp-probe-stderr.txt').write_text(''.join(errors),encoding='utf-8')