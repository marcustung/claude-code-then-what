"""Day 25: Claude Code builds a Grafana business dashboard with gcx and the create-dashboard Skill.
Reconciled data is published by publish_to_grafana.py (looped in the background during the run)."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
SKILL = Path.home()/'.claude/skills/create-dashboard'
EDITOR_CFG = os.path.join(os.environ['TEMP'], 'day25-gcx-editor.yaml')

w = ROOT/'runs-claude-dashboard'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); w.mkdir(parents=True)
shutil.copy2(SPEC, w/'notification-contract.md')
plug = w.parent/(w.name+'-plugin')
shutil.copytree(SKILL, plug/'skills/create-dashboard')
(plug/'.claude-plugin').mkdir(parents=True)
(plug/'.claude-plugin/plugin.json').write_text(json.dumps({'name': 'gcx-dash', 'version': '0.1.0', 'description': 'gcx create-dashboard Skill'}), encoding='utf-8')

prompt = """這是本機教學用的 Grafana（只有本機，不是公司環境）。只讀寫目前目錄，不要讀父目錄。

情境：早上打開 Grafana，我要先知道「哪些訂單取消後的通知工作還沒完成，今天先查哪一批」。CPU、API 延遲回答不了這個問題。

通知要怎樣才算完成，見 notification-contract.md。逐筆對帳已經由固定程式算好，結果送進了這個 Grafana，服務名稱是 day25-work-view（Prometheus 的 job 標籤、Loki 的 service_name）。有哪些指標、欄位、輪次，請你自己用 gcx 探索。

請用 gcx 建一個 Dashboard，UID 固定為 day25-work-view，標題自訂，可使用 create-dashboard Skill。要求：
- 每一輪都要看得出：應完成多少、確認完成多少、完成率、狀態；不能判斷的地方要讓人看得出「資料不足」，不要補成 0 或綠燈。
- 要能看到尚未完成的事件清單（帶通知 ID），讓人知道先查哪一批。
- 建好後，用 gcx 實際執行每個面板的查詢，確認數字合理。
- 把最後的 Dashboard 定義存成目前目錄的 dashboard.json（或你用來 push 的檔案）。

不要建立其他 Dashboard，也不要修改或刪除既有的 Dashboard 與資料來源。最後用繁體中文說明：每個面板回答什麼、用了哪些指標、為什麼這樣算完成率、你刻意沒用哪些指標、還不確定的地方。"""
(w/'prompt.txt').write_text(prompt, encoding='utf-8')

subs = ['datasources list', 'datasources get', 'datasources prometheus', 'datasources loki', 'metrics query', 'metrics labels', 'metrics metadata',
        'logs query', 'logs labels', 'logs series', 'resources push', 'resources get', 'resources validate', 'resources list-types', 'resources list-examples',
        'resources pull', 'dashboards create', 'dashboards update', 'dashboards get', 'dashboards list', 'dashboards search', 'dashboards snapshot', 'agent skills get']
allow = ['Read', 'Grep', 'Glob', 'Write', 'Edit', 'Skill'] + [f'Bash(gcx {s}:*)' for s in subs]
args = ['claude', '-p', prompt, '--model', 'sonnet', '--effort', 'medium', '--restricted',
        '--tools', 'Read,Grep,Glob,Write,Edit,Bash,Skill', '--allowedTools', ','.join(allow),
        '--setting-sources', 'project', '--settings', json.dumps({'disableAllHooks': True, 'autoMemoryEnabled': False}),
        '--strict-mcp-config', '--permission-mode', 'acceptEdits', '--plugin-dir', str(plug),
        '--output-format', 'stream-json', '--verbose', '--no-session-persistence', '--max-budget-usd', '3']
pub = subprocess.Popen([sys.executable, str(ROOT/'publish_to_grafana.py'), '--loop', '30'], cwd=ROOT,
                       stdout=(w.parent/(w.name+'-publish.log')).open('w', encoding='utf-8'), stderr=subprocess.STDOUT, env={**os.environ, 'PYTHONUTF8': '1'})
t0 = time.time()
try:
    with (w/'trace.jsonl').open('w', encoding='utf-8') as out, (w/'stderr.txt').open('w', encoding='utf-8') as err:
        p = subprocess.run(args, cwd=w, stdout=out, stderr=err, timeout=1800,
                           env={**os.environ, 'PYTHONUTF8': '1', 'GCX_CONFIG': EDITOR_CFG})
finally:
    pass  # keep publishing; the grader and screenshot need fresh samples. Stop it after grading.
res = {}
for l in (w/'trace.jsonl').read_text(encoding='utf-8').splitlines():
    d = json.loads(l)
    if d.get('type') == 'result': res = d
(w/'answer.md').write_text(res.get('result', ''), encoding='utf-8')
(w/'execution.json').write_text(json.dumps({'exit_code': p.returncode, 'elapsed_seconds': round(time.time()-t0, 2), 'cost_usd': res.get('total_cost_usd'),
    'turns': res.get('num_turns'), 'model': 'sonnet', 'allowed': allow, 'publisher_pid': pub.pid}, indent=2), encoding='utf-8')
(ROOT/'latest-claude-dashboard-run.txt').write_text(str(w.relative_to(ROOT)), encoding='utf-8')
print('Claude exit', p.returncode, w, 'publisher pid', pub.pid)
