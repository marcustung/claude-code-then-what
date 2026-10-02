from pathlib import Path
import subprocess,json,hashlib,time,shutil,datetime
L=Path(__file__).resolve().parent
CLI=Path.home()/'.local/bin/claude.exe'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def hashes(p):return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
def main():
 out=L/'runs'/datetime.datetime.now().strftime('next-task-%Y%m%d-%H%M%S');out.mkdir(parents=True)
 save(out/'protocol.json',{'fixture':'synthetic ticket and sender event, not live service execution','cases':['before','after'],'constant':'same ticket, event, prompt, r2 code, model/tools; new applicability page plus index entry only','expectations':['read code and wiki','identify sync SendOnce path','receiver outcome unknown','do not authorize resend or use repeated cancel as resend','next step identifies notification_id, required evidence and decision role'],'sample':'one each; no accuracy or time savings estimate'})
 print(out,flush=True)
 for case in ['before','after']:
  d=out/case;w=d/'workspace';w.mkdir(parents=True);(w/'sources').mkdir()
  for name in ['Program.cs','Cancellation.cs','design-review.md']:shutil.copy2(L/'sources'/name,w/'sources'/name)
  shutil.copytree(L/'fixtures/wiki-before-next-task' if case=='before' else L/'fixtures/wiki-next-task-accepted',w/'wiki')
  for f in (w/'wiki').glob('*.md'):
   s=f.read_text(encoding='utf-8').replace('，及 [既有 Claude 回答](../sources/claude-answer.md)','');f.write_text(s,encoding='utf-8')
  save(w/'ticket.json',{'kind':'SYNTHETIC teaching ticket, not production incident','request':'使用者說取消訂單後沒有收到通知；API 回200，已有 notify_sent。請判斷是否需要補送，交給下一位RD接著處理。','order_id':'demo-order-18','notification_id':'demo-notify-18','reported_version':'delivery-hardening-local-r2','provided_code_version':'delivery-hardening-local-r2','time_window':'2026-10-01T00:00:00Z/2026-10-01T00:05:00Z','environment':'synthetic local exercise','available':'sender event only; receiver logs, deployed configuration proof, resend contract and named Owner not provided','permission':'read-only; no live tools or actions'})
  save(w/'sender-event.json',{'fixture':'SYNTHETIC shaped after Program.cs event; not actual captured log','event':'notify_sent','order_id':'demo-order-18','notification_id':'demo-notify-18','sync':True})
  save(w/'mcp.json',{'mcpServers':{}})
  prompt='讀 ticket.json、sender-event.json，從 wiki/INDEX.md 選相關知識並核對來源程式。回答這張工單：已確認什麼、尚缺什麼、下一步查哪裡及用什麼條件、是否可以補送、需要誰決定。每項附來源，不編造部署資訊與授權。只讀此工作目錄，不執行指令、不修改檔案、不呼叫外部系統。繁體中文600字內。'
  (d/'prompt.txt').write_text(prompt,encoding='utf-8');before=hashes(w);save(d/'input-manifest.json',before)
  cmd=[str(CLI),'-p',prompt,'--model','sonnet','--effort','medium','--restricted','--tools','Read,Grep,Glob','--allowedTools','Read,Grep,Glob','--setting-sources','project','--strict-mcp-config','--mcp-config',str(w/'mcp.json'),'--output-format','stream-json','--verbose','--no-session-persistence','--max-budget-usd','2']
  save(d/'command.json',cmd);start=time.monotonic()
  with (d/'trace.jsonl').open('w',encoding='utf-8') as o,(d/'stderr.txt').open('w',encoding='utf-8') as e:
   try:rc=subprocess.run(cmd,cwd=w,stdout=o,stderr=e,timeout=300).returncode
   except subprocess.TimeoutExpired:rc=124
  final={};calls=[]
  for line in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines():
   try:v=json.loads(line)
   except ValueError:continue
   if v.get('type')=='result':final=v
   for block in (v.get('message') or {}).get('content',[]) or []:
    if isinstance(block,dict) and block.get('type')=='tool_use':calls.append(block)
  save(d/'result.json',final);save(d/'tool-calls.json',calls);(d/'answer.md').write_text(final.get('result',''),encoding='utf-8')
  save(d/'execution.json',{'returncode':rc,'seconds':round(time.monotonic()-start,2),'unchanged':before==hashes(w),'is_error':final.get('is_error'),'cost_usd':final.get('total_cost_usd'),'num_turns':final.get('num_turns')})
  print(case,rc,final.get('is_error'),flush=True)
  if rc or final.get('is_error'):raise RuntimeError('incomplete run; outputs retained')
if __name__=='__main__':main()
