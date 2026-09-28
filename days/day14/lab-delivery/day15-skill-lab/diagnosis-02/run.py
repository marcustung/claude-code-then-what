from pathlib import Path
import subprocess,json,time,hashlib
b=Path(__file__).resolve().parent;w=b/'workspace';o=b/'records';o.mkdir()
prompt="""唯讀分析本目錄的教學訂單服務。讀 plan.md、兩組 report.json 與 k6-summary.json、receipts.json 和 logs.jsonl，以及 src/Api/Program.cs、src/Domain/Cancellation.cs。追出取消回應到通知接收的呼叫路徑，附檔名與精確行號。分開列已確認事實、推論、尚缺量測。解釋為何 API 門檻全過而 slow 組截止未完成，確認通知處理是否串行、是否等待 HTTP。300ms 是人為注入，20秒是教學觀察期限，不能宣稱發現未知Production根因或永久遺失。用通知ID核對摘要時注意截止快照與關閉後日誌的時間邊界。提出下一個查核，不修改、不執行、不宣稱修復。輸出繁體中文，最多1000字。"""
(o/'prompt.txt').write_text(prompt,encoding='utf-8')
args=[str(Path.home()/'.local/bin/claude.exe'),'-p',prompt,'--model','sonnet','--effort','medium','--restricted','--tools','Read,Grep,Glob','--allowedTools','Read,Grep,Glob','--setting-sources','','--strict-mcp-config','--mcp-config',str(b/'empty-mcp.json'),'--output-format','stream-json','--verbose','--no-session-persistence','--max-budget-usd','3']
(o/'command.json').write_text(json.dumps(args,ensure_ascii=False),encoding='utf-8')
(o/'manifest.json').write_text(json.dumps({str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in w.rglob('*') if p.is_file()},indent=2),encoding='utf-8')
t=time.monotonic()
with (o/'trace.jsonl').open('w',encoding='utf-8') as out,(o/'stderr.txt').open('w',encoding='utf-8') as err:
 r=subprocess.run(args,cwd=w,stdout=out,stderr=err,timeout=240)
(o/'execution.json').write_text(json.dumps({'exit':r.returncode,'seconds':time.monotonic()-t}))
for line in (o/'trace.jsonl').read_text(encoding='utf-8').splitlines():
 e=json.loads(line)
 if e.get('type')=='result':
  (o/'result.json').write_text(json.dumps(e,ensure_ascii=False),encoding='utf-8')
  (o/'analysis.md').write_text(e.get('result',''),encoding='utf-8')
print('Saved; exit',r.returncode)
