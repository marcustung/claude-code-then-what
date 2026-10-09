"""Day 25 round 4: user's acceptance of v3 failed; hand the user's own words back to Claude and build day25-work-view-v4.
Reconciled data is published by publish_to_grafana.py (looped in the background during the run)."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
SKILL = Path.home()/'.claude/skills/create-dashboard'
EDITOR_CFG = os.path.join(os.environ['TEMP'], 'day25-gcx-editor.yaml')

w = ROOT/'runs-claude-dashboard'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-v4'); w.mkdir(parents=True)
first = ROOT/(ROOT/'latest-claude-dashboard-v3title-run.txt').read_text().strip()
shutil.copy2(first/'dashboard.json', w/'previous-version.json')
shutil.copy2(SPEC, w/'notification-contract.md')
plug = w.parent/(w.name+'-plugin')
shutil.copytree(SKILL, plug/'skills/create-dashboard')
(plug/'.claude-plugin').mkdir(parents=True)
(plug/'.claude-plugin/plugin.json').write_text(json.dumps({'name': 'gcx-dash', 'version': '0.1.0', 'description': 'gcx create-dashboard Skill'}), encoding='utf-8')

prompt = """這是本機教學用的 Grafana（只有本機，不是公司環境）。只讀寫目前目錄，不要讀父目錄。

previous-version.json 是第三版 Dashboard（UID day25-work-view-v3）。使用者驗收沒有通過，原話是：
- 「哪幾批要處理 》有沒問題」
- 「下一個問題是什麼」
- 「dashboard 的文字都要簡單扼要，像是幾批都是不合格的用詞」
- 「都儘量精簡：有問題/沒問題>狀態」「對方回得慢：成功失敗、紀錄」

請據此建立第四版，UID 為 day25-work-view-v4，放在資料夾 day25（folder UID：day25）。不要修改或刪除其他 Dashboard。
設計原則：
0. 這張圖想回答的問題貫穿全部：主標題就是那個問題，要短。
1. 第一層先回答是非題「有沒有問題」，並直接說出是哪一項有問題；不要用「幾批」計數。使用者補充：「有問題／沒問題」改成一欄「狀態」，值只用結果詞：成功、失敗、紀錄不全（資料裡的 status_text 標籤，照實顯示）；項目名稱照資料顯示。
2. 每一層的標題都是一個簡短問題，回答完會自然引出下一層要問的問題，直到「交給誰、下一步」。
3. 所有文字簡單扼要：標題、欄位、說明都越短越好，不出現指標名稱、英文代碼、工程術語，也不要「批」「輪」這類計數字。
4. 沿用第三版做對的部分：燈號（紅＝失敗、灰＝紀錄不全、綠＝成功）、進度條（對方收到 ／ 應完成；資料不足不畫）、下一步與負責人照資料呈現、明細需要時才展開、通知編號保留在明細。

資料在服務 day25-work-view（Prometheus 的 job、Loki 的 service_name）；各項名稱、流程各段、下一步與負責人的文字剛縮短過，請直接顯示資料裡的文字，不要改寫。預設時間範圍設成最近 5 分鐘。本機 Grafana 沒有截圖用的 renderer。
環境限制：允許清單一次只認一個 gcx 指令，不要用 ;、&&、| 串接，否則整串會被擋下。

建好後用 gcx 實際執行每個面板的查詢確認數字，把最後的定義存成 dashboard.json。最後用繁體中文列出：主標題、每一層的問題與它引出的下一個問題、你刪掉了哪些字。"""
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
(ROOT/'latest-claude-dashboard-v4-run.txt').write_text(str(w.relative_to(ROOT)), encoding='utf-8')
print('Claude exit', p.returncode, w, 'publisher pid', pub.pid)
