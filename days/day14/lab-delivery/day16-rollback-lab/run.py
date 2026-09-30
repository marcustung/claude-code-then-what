# -*- coding: utf-8 -*-
"""Day 16：回復演練紀錄的唯讀判讀。

問題取自 Day 16 正文已寫好的那段提示：分開回答程式是否恢復、下游是否恢復、
故障期間資料是否處理完成，每項附紀錄來源，列出仍不能結案的工作。

刻意不給的東西：我的結論、正文、「rollback 不還原資料」這個說法。
workspace 只有回復演練的原始紀錄、兩個包的身分、新版程式與演練腳本。
"""
from pathlib import Path
import subprocess, json, time, hashlib

b = Path(__file__).resolve().parent
w = b / 'workspace'
o = b / 'records'
o.mkdir(exist_ok=True)

prompt = """唯讀判讀本目錄的一次本機部署演練紀錄。

先讀 runs/acceptance-rollback-01/ 下的 report.json、requests.json、receipts.json、incident.json，
以及 before/、updated/、rolled-back/ 三個階段各自的 deployment.json 與 logs.jsonl。
需要時再讀 rehearse-release.py、release-next-change.json、release-next/src/Api/Program.cs、
release-next/src/Domain/Cancellation.cs。

這次演練依序做了三件事：啟動舊包、換成新包並注入下游失敗、再回復舊包。

請分開回答三個問題，不要合併成一句「已恢復」：
1. 程式是否恢復？依據是哪一筆紀錄？
2. 下游（通知接收端）是否恢復？依據是哪一筆紀錄？
3. 故障期間產生的資料，工作是否處理完成？依據是哪一筆紀錄？

每一項都要附出處（檔名與精確行號或 JSON 路徑），並標明它屬於下列哪一種：
已被這次演練實際驗證、只能從紀錄推論、這次沒有量測。

接著列出「仍不能結案的工作」：這次演練結束後，還有哪些事情沒有人處理，
以及要處理它們需要先知道什麼。

注意邊界，不要越過紀錄說話：
- 下游失敗是人為注入的假接收端回應，不是新發現的程式缺陷，也不是生產事故。
- 回復那一步同時換回程式與恢復接收端，變因沒有隔離。
- 本服務的訂單存在程序記憶體；這是教學環境的設計，不要推論成 Production 的資料遺失事故。
- report.json 的 passed 代表演練把預期狀態查清楚了，不代表服務具備上線條件。

最後提出下一個該查核的項目。不修改任何檔案、不執行任何指令、不宣稱已修復。
輸出繁體中文，最多 1200 字。"""

(o / 'prompt.txt').write_text(prompt, encoding='utf-8')

args = [
    str(Path.home() / '.local/bin/claude.exe'), '-p', prompt,
    '--model', 'sonnet', '--effort', 'medium', '--restricted',
    '--tools', 'Read,Grep,Glob', '--allowedTools', 'Read,Grep,Glob',
    '--setting-sources', '', '--strict-mcp-config',
    '--mcp-config', str(b / 'empty-mcp.json'),
    '--output-format', 'stream-json', '--verbose',
    '--no-session-persistence', '--max-budget-usd', '3',
]
(o / 'command.json').write_text(json.dumps(args, ensure_ascii=False), encoding='utf-8')
(o / 'manifest.json').write_text(json.dumps(
    {str(p.relative_to(w)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
     for p in sorted(w.rglob('*')) if p.is_file()}, indent=2), encoding='utf-8')

t = time.monotonic()
with (o / 'trace.jsonl').open('w', encoding='utf-8') as out, \
     (o / 'stderr.txt').open('w', encoding='utf-8') as err:
    r = subprocess.run(args, cwd=w, stdout=out, stderr=err, timeout=420)

(o / 'execution.json').write_text(json.dumps(
    {'exit': r.returncode, 'seconds': round(time.monotonic() - t, 1),
     'mode': 'read-only analysis', 'changed': []}, ensure_ascii=False), encoding='utf-8')

for line in (o / 'trace.jsonl').read_text(encoding='utf-8').splitlines():
    e = json.loads(line)
    if e.get('type') == 'result':
        (o / 'result.json').write_text(json.dumps(e, ensure_ascii=False), encoding='utf-8')
        (o / 'analysis.md').write_text(e.get('result', ''), encoding='utf-8')
print('exit', r.returncode, '|', round(time.monotonic() - t, 1), 's')
