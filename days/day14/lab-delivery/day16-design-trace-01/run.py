# -*- coding: utf-8 -*-
"""Day 16：把設計核對當成出事時的查核地圖。

Day 10 留下的 design-input/design-review.md 有七條核對結果，其中第 1 條寫了
API 到通知的呼叫路徑與行號，第 4、5 條寫了並行與持久性的限制。
Day 16 的回復演練是在不看這份設計的情況下跑的。

這次問的是：沿著那份設計，這次工作實際停在哪一段，
以及設計裡有沒有哪一條已經預告了演練撞到的事。

刻意不給的：Day 16 正文、我的結論、先前那次唯讀判讀的結果。
"""
from pathlib import Path
import subprocess, json, time, hashlib

b = Path(__file__).resolve().parent
w = b / 'workspace'
o = b / 'records'
o.mkdir(exist_ok=True)

prompt = """這個資料夾有兩種東西：一份開發前留下的設計核對（design-input/），
以及一次本機部署演練的紀錄（runs/acceptance-rollback-01/）。
演練依序做了三件事：啟動舊包、換成新包並注入下游失敗、再回復舊包。
src/ 有新版的兩支程式可以對照行號。

先讀 design-input/design-review.md 與 scope-handoff.md，再讀演練紀錄。

回答三件事：

1. **沿著設計寫的那條路徑，這次工作實際停在哪一段？**
   design-review.md 第 1 條寫了從 API 到通知的呼叫順序與行號。
   請指出這次失敗的那一筆工作走到哪一步就沒有再往前，附紀錄出處與程式行號。
   注意新版程式的行號可能與設計當時不同，若對不上請明說。

2. **設計裡有哪幾條已經預告了這次演練撞到的事？**
   逐條指出（用「第 N 條」），並附演練紀錄裡對應的那一筆。
   如果某一條預告了、但這次演練沒有驗到，也要說。

3. **設計裡有哪幾條，這次演練完全沒有碰到？**
   這些是「設計提過、但至今沒有任何執行證據」的部分。

邊界：下游失敗是人為注入的假接收端回應，不是新發現的程式缺陷；
回復那一步同時換回程式與接收端，變因沒有隔離；
訂單存在程序記憶體是教學環境的設計，不要推論成 Production 資料遺失事故。
設計核對本身是教學分析，不是業務核准。

不修改檔案、不執行指令、不宣稱已修復。輸出繁體中文，最多 1200 字。"""

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
        (o / 'trace.md').write_text(e.get('result', ''), encoding='utf-8')
print('exit', r.returncode, '|', round(time.monotonic() - t, 1), 's')
