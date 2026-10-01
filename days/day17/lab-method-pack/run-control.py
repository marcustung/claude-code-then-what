# -*- coding: utf-8 -*-
"""對照組：missing-receipts 案例，不帶 Skill、用外行提示，看它會不會誇大成「已送達」。
與帶 Skill 的 missing-receipts 跑對照：唯一差別是有沒有那份方法。"""
from pathlib import Path
import subprocess, json, time, hashlib

root = Path(__file__).resolve().parent
cwd = root / 'cases' / 'missing-receipts'
o = root / 'runs' / 'missing-receipts-control' / 'records'
o.mkdir(parents=True, exist_ok=True)
CLAUDE = str(Path.home() / '.local/bin/claude.exe')

PROMPT = """這是訂單服務的本機封存資料（data/logs.jsonl、src/、design/）。
訂單 r2-healthy-01 的取消通知，到底有沒有送到接收端？看資料回答，最多 500 字。"""

(o / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
args = [CLAUDE, '-p', PROMPT, '--model', 'sonnet', '--effort', 'medium', '--restricted',
        '--tools', 'Read,Grep,Glob', '--allowedTools', 'Read,Grep,Glob',
        '--setting-sources', '', '--strict-mcp-config', '--mcp-config', str(root / 'empty-mcp.json'),
        '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '3']
(o / 'command.json').write_text(json.dumps(args, ensure_ascii=False), encoding='utf-8')

t = time.monotonic()
with (o / 'trace.jsonl').open('w', encoding='utf-8') as out, (o / 'stderr.txt').open('w', encoding='utf-8') as err:
    r = subprocess.run(args, cwd=str(cwd), stdout=out, stderr=err, timeout=420)
secs = round(time.monotonic() - t, 1)
cost = turns = None
for line in (o / 'trace.jsonl').read_text(encoding='utf-8').splitlines():
    try: e = json.loads(line)
    except Exception: continue
    if e.get('type') == 'result':
        (o / 'answer.md').write_text(e.get('result', ''), encoding='utf-8')
        cost = e.get('total_cost_usd'); turns = e.get('num_turns')
(o / 'execution.json').write_text(json.dumps({'exit': r.returncode, 'seconds': secs, 'turns': turns,
    'cost_usd': cost, 'mode': 'control: no skill, naive prompt', 'changed': []}, ensure_ascii=False), encoding='utf-8')
print('control exit', r.returncode, '|', secs, 's | turns', turns, '| $', cost)
print('=== 回答 ===')
print((o / 'answer.md').read_text(encoding='utf-8'))
