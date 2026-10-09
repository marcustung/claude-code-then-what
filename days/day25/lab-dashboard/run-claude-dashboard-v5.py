"""Day 25 round 5: redesign agreed with the user (only problem items flow down) plus newly published facts; builds day25-work-view-v5.
Reconciled data is published by publish_to_grafana.py (looped in the background during the run)."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
SKILL = Path.home()/'.claude/skills/create-dashboard'
EDITOR_CFG = os.path.join(os.environ['TEMP'], 'day25-gcx-editor.yaml')

w = ROOT/'runs-claude-dashboard'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-v5'); w.mkdir(parents=True)
first = ROOT/(ROOT/'latest-claude-dashboard-v4-run.txt').read_text().strip()
shutil.copy2(first/'dashboard.json', w/'previous-version.json')
shutil.copy2(SPEC, w/'notification-contract.md')
plug = w.parent/(w.name+'-plugin')
shutil.copytree(SKILL, plug/'skills/create-dashboard')
(plug/'.claude-plugin').mkdir(parents=True)
(plug/'.claude-plugin/plugin.json').write_text(json.dumps({'name': 'gcx-dash', 'version': '0.1.0', 'description': 'gcx create-dashboard Skill'}), encoding='utf-8')

prompt = """這是本機教學用的 Grafana（只有本機，不是公司環境）。只讀寫目前目錄，不要讀父目錄。

previous-version.json 是第四版 Dashboard（UID day25-work-view-v4），使用者認可它的問題串接與用詞，但審查發現兩個問題：
1. 三張表都出現捲軸，最後一列被切掉一半。
2. 同樣五個項目重複列了三次；後面幾層也列出成功的項目。

使用者同意的重新設計（請照這個結構做，查詢與面板由你決定）：

    取消通知送到了嗎？
    有問題嗎？
      ● 失敗      漏送通知
      ● 紀錄不全   回得慢・資料未齊
      ● 成功      修好後重跑、正常、回得慢・已收齊        ← 成功的只在這裡出現一次，只列名稱、不計數
    卡在哪？（只列紅、灰的項目）
      漏送通知       取消成功 9 → 排進待送 9 → 系統說已送 9 → 對方收到 3 ◀ 卡在這
                     進度 33%
      回得慢・資料未齊 紀錄不全，看不出卡在哪
    誰處理？（只列紅、灰的項目）
      漏送通知       通知服務   查沒收到的原因
      回得慢・資料未齊 資料平台   先補資料，再判斷
    ▸ 哪幾筆？（收合，點開才看）

原則：只把有問題的項目往下傳；面板高度跟著列數，不能出現捲軸；文字簡短、不用「批」「輪」與術語；燈號紅＝失敗、灰＝紀錄不全、綠＝成功。

這次資料多了幾項，請用在最需要的地方，文字照資料顯示、不要改寫：
- work_status 多了 stuck_detail（例如「6 筆停在「延後」，之後沒有再送」）與 data_time（資料時間，重放的會註明）。
- work_refund_unmatched：尚未對上的退款通知筆數。退款通知代表客人付了錢卻沒被告知，比一般通知急。
- Loki 事件多了 refund（退款／一般）、last_step（最後停在哪一步）、cancel_time、waited。

請建立第五版：UID day25-work-view-v5，資料夾 day25（folder UID：day25），預設時間範圍最近 5 分鐘。不要修改或刪除其他 Dashboard。本機 Grafana 沒有截圖用的 renderer。
環境限制：允許清單一次只認一個 gcx 指令，不要用 ;、&&、| 串接。

建好後用 gcx 實際執行每個面板的查詢確認數字，把最後的定義存成 dashboard.json。最後用繁體中文說明：新資料各用在哪裡、為什麼，以及你怎麼避免捲軸。"""
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
(ROOT/'latest-claude-dashboard-v5-run.txt').write_text(str(w.relative_to(ROOT)), encoding='utf-8')
print('Claude exit', p.returncode, w, 'publisher pid', pub.pid)
