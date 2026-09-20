from pathlib import Path
import subprocess,json,datetime,hashlib
lab=Path(__file__).parent
cli=r"<HOME>\.local\bin\claude.exe"
def run(n):
 prompt=(lab/f"stage{n}-prompt.txt").read_text(encoding="utf-8")
 args=[cli,"-p",prompt,"--model","sonnet","--effort","low","--safe-mode","--tools","Read","--allowedTools","Read","--strict-mcp-config","--mcp-config",'{"mcpServers":{}}',"--output-format","stream-json","--verbose","--no-session-persistence","--max-budget-usd","1"]
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (lab/f"stage{n}-trace.jsonl").open("w",encoding="utf-8") as out,(lab/f"stage{n}-stderr.txt").open("w",encoding="utf-8") as err:
  p=subprocess.run(args,cwd=lab/"inputs",stdout=out,stderr=err,encoding="utf-8",timeout=240)
 meta={"start":start,"end":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit":p.returncode,"args":args,"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest()}
 (lab/f"stage{n}-meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
 rows=[json.loads(x) for x in (lab/f"stage{n}-trace.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
 result=next((x for x in reversed(rows) if x.get("type")=="result"),None)
 if p.returncode or not result or result.get("is_error"): raise RuntimeError(f"stage{n} failed; originals retained")
 (lab/f"stage{n}-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 (lab/f"stage{n}-answer.md").write_text(result.get("result",""),encoding="utf-8")
 print(f"stage{n} completed",flush=True)
run(1)
(lab/"inputs/previous-draft.md").write_text((lab/"stage1-answer.md").read_text(encoding="utf-8"),encoding="utf-8")
(lab/"inputs/decision.md").write_text("DEMO-DECISION-01: 純教學假設，非公司政策、非真實 Owner 核准。對已付款、未出貨、尚未取消的訂單：取消功能只將 Cancelled 設為 true；退款交另一流程決定，本功能 RefundRequested=false。不得呼叫付款服務。其他行為仍須另行確認。",encoding="utf-8")
(lab/"stage2-prompt.txt").write_text("讀取 spec.md、previous-draft.md 與 decision.md。依新增決策修訂驗收草稿，列出來源、具體 Given/When/Then 案例、相對前稿的變更與仍未決事項。保留決策的教學性質。只交草稿，不實作、不執行測試，也不要宣稱真實 Owner 已批准。",encoding="utf-8")
run(2)
