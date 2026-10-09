"""Day 25: ask Claude Code to build the work view from the spec and raw run files only.
Answers (build.py, view.json, check.json, slo-report.json, final-states.json, claude-criteria.md) are not copied in."""
from pathlib import Path
from datetime import datetime, timezone
import subprocess, json, os, shutil, time

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent/'order-cancel-lifecycle/evidence/runs'
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
RUNS = ['missing-notification-20260921-193704', 'missing-notification-20260921-193835', 'slow-sync-control-20260923-191636']
FILES = ['manifest.json', 'logs.jsonl', 'receipts.jsonl', 'metrics.txt', 'requests.jsonl']

w = ROOT/'runs-claude'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
w.mkdir(parents=True)
for name in RUNS:
    (w/'data'/name).mkdir(parents=True)
    for f in FILES:
        if (SOURCE/name/f).exists(): shutil.copy2(SOURCE/name/f, w/'data'/name/f)
shutil.copy2(SPEC, w/'notification-contract.md')

prompt = """這是本機 .NET 教學服務的歷史紀錄，不是公司資料。只讀寫目前目錄，不要讀父目錄。

情境：早上打開 Dashboard，我要先知道「哪些訂單取消後的通知工作還沒完成，今天先查哪一批」。CPU、API 延遲回答不了這個問題。

請依 notification-contract.md 決定什麼算「該完成的通知」與「已完成」，自己讀 data/ 下三輪紀錄（manifest.json、logs.jsonl、receipts.jsonl、metrics.txt、requests.jsonl）找出可用的欄位，再寫 reconcile.py：

- 執行方式：python reconcile.py <run 資料夾> [<run 資料夾> ...] --out <輸出資料夾>
- 輸出 <輸出資料夾>/view.json：每輪一個物件，欄位 run_id、expected（應完成數）、received（已確認完成數）、unmatched（尚未對上數）、status、reason、events（每筆 order_id、request_id、notification_id、state）。不能判斷的數字用 null，不要補 0。
- status 只能是四種之一：matched（全部對上）、investigate（有確定要查的事件）、waiting（還在處理，尚不能下結論）、unknown（資料不足，無法判斷）。
- 另輸出 index.html：讓人一眼看出每輪要先做什麼，並能展開未對上的事件清單。

寫完請對 data/ 三輪實際執行一次，輸出到 out/。最後用繁體中文說明：你的分母怎麼定、怎麼比對、哪些情況判 unknown 或 waiting、每輪結果與依據、還不確定的地方。不要修改 data/ 與 notification-contract.md。"""
(w/'prompt.txt').write_text(prompt, encoding='utf-8')

allow = ['Read', 'Grep', 'Glob', 'Write', 'Edit', 'Bash(python reconcile.py:*)', 'Bash(python -c:*)']
args = ['claude', '-p', prompt, '--model', 'sonnet', '--effort', 'medium', '--restricted',
        '--tools', 'Read,Grep,Glob,Write,Edit,Bash', '--allowedTools', ','.join(allow),
        '--setting-sources', 'project', '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}),
        '--strict-mcp-config', '--permission-mode', 'acceptEdits', '--output-format', 'stream-json', '--verbose',
        '--no-session-persistence', '--max-budget-usd', '3']
start = time.time()
with (w/'trace.jsonl').open('w', encoding='utf-8') as out, (w/'stderr.txt').open('w', encoding='utf-8') as err:
    p = subprocess.run(args, cwd=w, stdout=out, stderr=err, env=dict(os.environ, PYTHONUTF8='1'), timeout=1200)
(w/'execution.json').write_text(json.dumps({'exit_code': p.returncode, 'elapsed_seconds': round(time.time()-start, 2),
    'model': 'sonnet', 'allowed': allow, 'budget_usd': 3}, indent=2), encoding='utf-8')
(ROOT/'latest-claude-run.txt').write_text(str(w.relative_to(ROOT)), encoding='utf-8')
print('Claude exit', p.returncode, w)
