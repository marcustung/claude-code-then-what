# -*- coding: utf-8 -*-
"""Day 17：把 trace-notification 方法包真的跑一次。

開新 session（headless、唯讀），對兩個案例各跑一次，看方法離開原對話後守不守得住判準：
  complete        —— 有 receipts，應把接收端標 confirmed 並附來源
  missing-receipts —— 無 receipts，應把接收端標 unknown，不能寫成「未送達」

每案 cwd 設在案例目錄，讓專案 Skill（.claude/skills/trace-notification）被發現。
工具只開 Read/Grep/Glob/Skill，沒有 Edit/Bash，MCP 指空設定檔。逐回合軌跡與用量完整保存。
"""
from pathlib import Path
import subprocess, json, time, hashlib

root = Path(__file__).resolve().parent
empty_mcp = root / 'empty-mcp.json'
CLAUDE = str(Path.home() / '.local/bin/claude.exe')

PROMPT = """使用 trace-notification 這個 Skill（在 .claude/skills/trace-notification/SKILL.md），照它的查核迴圈與輸出格式做。

這次事件（見 task.json）：
- order_id: r2-healthy-01
- 部署版本: delivery-hardening-local-r2
- 環境: 本機教學封存，非正式環境
- 可用資料都在本目錄：data/（logs.jsonl、若有 receipts.json）、src/（Program.cs、Cancellation.cs）、design/（design-review.md）
- 沒有連到 Log server，用本目錄的封存資料查。

沿 API 與背景通知查核：先對程式與版本，再用 order_id 從 log 找 notification_id，串起發送端與接收端。
分開 API 結果、發送端觀察、接收端佐證。接收端只有在有對應收據來源時才可標 confirmed；
查不到接收端資料標 unknown，不要寫成一定未送達。最後照 SKILL 要求輸出 JSON。

只查詢與分析，不修改檔案、不執行指令、不補送、不結案。輸出繁體中文，最多 1000 字。"""


def run_case(name):
    cwd = root / 'cases' / name
    o = root / 'runs' / name / 'records'
    o.mkdir(parents=True, exist_ok=True)
    (o / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
    args = [
        CLAUDE, '-p', PROMPT,
        '--model', 'sonnet', '--effort', 'medium', '--restricted',
        '--tools', 'Read,Grep,Glob,Skill', '--allowedTools', 'Read,Grep,Glob,Skill',
        '--setting-sources', 'project', '--strict-mcp-config',
        '--mcp-config', str(empty_mcp),
        '--output-format', 'stream-json', '--verbose',
        '--no-session-persistence', '--max-budget-usd', '3',
    ]
    (o / 'command.json').write_text(json.dumps(args, ensure_ascii=False), encoding='utf-8')
    (o / 'manifest.json').write_text(json.dumps(
        {str(p.relative_to(cwd)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(cwd.rglob('*')) if p.is_file() and '__pycache__' not in str(p)},
        indent=2, ensure_ascii=False), encoding='utf-8')

    t = time.monotonic()
    with (o / 'trace.jsonl').open('w', encoding='utf-8') as out, \
         (o / 'stderr.txt').open('w', encoding='utf-8') as err:
        r = subprocess.run(args, cwd=str(cwd), stdout=out, stderr=err, timeout=420)
    secs = round(time.monotonic() - t, 1)

    tools = []
    cost = turns = None
    for line in (o / 'trace.jsonl').read_text(encoding='utf-8').splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        for c in (e.get('message', {}) or {}).get('content', []) or []:
            if isinstance(c, dict) and c.get('type') == 'tool_use':
                tools.append(c.get('name'))
        if e.get('type') == 'result':
            (o / 'result.json').write_text(json.dumps(e, ensure_ascii=False), encoding='utf-8')
            (o / 'trace-report.md').write_text(e.get('result', ''), encoding='utf-8')
            cost = e.get('total_cost_usd'); turns = e.get('num_turns')
    (o / 'execution.json').write_text(json.dumps(
        {'exit': r.returncode, 'seconds': secs, 'turns': turns, 'cost_usd': cost,
         'mode': 'read-only trace via trace-notification skill', 'changed': [],
         'tools': sorted(set(tools)), 'used_skill': 'Skill' in tools}, ensure_ascii=False), encoding='utf-8')
    print(f'[{name}] exit {r.returncode} | {secs}s | turns {turns} | ${cost} | tools {sorted(set(tools))}')


for case in ('complete', 'missing-receipts'):
    run_case(case)
