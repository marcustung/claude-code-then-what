"""Day 25 round 2: hand the fixed-check findings back to Claude as review feedback, then re-grade with check_claude.py.
The feedback describes the failing behaviour, not the expected implementation; fixtures stay outside the workdir."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
first = ROOT/sys.argv[1] if len(sys.argv) > 1 else ROOT/(ROOT/'latest-claude-run.txt').read_text().strip()
w = ROOT/'runs-claude'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-fix')
w.mkdir(parents=True)
for name in ['data', 'notification-contract.md', 'reconcile.py']:
    s = first/name
    (shutil.copytree if s.is_dir() else shutil.copy2)(s, w/name)

prompt = """這是本機 .NET 教學服務的歷史紀錄，不是公司資料。只讀寫目前目錄，不要讀父目錄。

目前目錄的 reconcile.py 是上一輪寫的對帳程式（介面與輸出欄位不變：python reconcile.py <run 資料夾>... --out <輸出資料夾>）。審查時，固定檢查用改造過的資料跑它，發現三個問題：

1. 接收端收據的筆數和 request_id 都對得上，但 notification_id 和發送端記錄的不同時，程式判成 matched。
2. 發送端紀錄裡完全沒有 notification_id 時，程式仍判成 matched。
3. slow-sync-control 那輪判成 waiting。這是 15 天前保存的快照，不會再有新收據進來；值班的人看到 waiting 只會繼續等。

請依 notification-contract.md 重新想清楚「什麼才算這則通知已完成」，修正 reconcile.py，對 data/ 三輪重跑輸出到 out/，用繁體中文說明改了什麼、為什麼。不要修改 data/ 與 notification-contract.md。"""
(w/'prompt.txt').write_text(prompt, encoding='utf-8')
allow = ['Read', 'Grep', 'Glob', 'Write', 'Edit', 'Bash(python reconcile.py:*)', 'Bash(python -c:*)']
args = ['claude', '-p', prompt, '--model', 'sonnet', '--effort', 'medium', '--restricted',
        '--tools', 'Read,Grep,Glob,Write,Edit,Bash', '--allowedTools', ','.join(allow),
        '--setting-sources', 'project', '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}),
        '--strict-mcp-config', '--permission-mode', 'acceptEdits', '--output-format', 'stream-json', '--verbose',
        '--no-session-persistence', '--max-budget-usd', '2']
t0 = time.time()
with (w/'trace.jsonl').open('w', encoding='utf-8') as out, (w/'stderr.txt').open('w', encoding='utf-8') as err:
    p = subprocess.run(args, cwd=w, stdout=out, stderr=err, env=dict(os.environ, PYTHONUTF8='1'), timeout=1200)
res = {}
for l in (w/'trace.jsonl').read_text(encoding='utf-8').splitlines():
    d = json.loads(l)
    if d.get('type') == 'result': res = d
(w/'answer.md').write_text(res.get('result', ''), encoding='utf-8')
(w/'execution.json').write_text(json.dumps({'exit_code': p.returncode, 'elapsed_seconds': round(time.time()-t0, 2), 'cost_usd': res.get('total_cost_usd'),
    'turns': res.get('num_turns'), 'model': 'sonnet', 'allowed': allow, 'first_round': first.name}, indent=2), encoding='utf-8')
print(w.relative_to(ROOT))
