"""Day 25 round 3: v2 principles plus traffic lights, progress bars and next step/owner; rebuilds as day25-work-view-v3.
Reconciled data is published by publish_to_grafana.py (looped in the background during the run)."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
SKILL = Path.home()/'.claude/skills/create-dashboard'
EDITOR_CFG = os.path.join(os.environ['TEMP'], 'day25-gcx-editor.yaml')

w = ROOT/'runs-claude-dashboard'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-v3'); w.mkdir(parents=True)
first = ROOT/(ROOT/'latest-claude-dashboard-v2-run.txt').read_text().strip()
shutil.copy2(first/'dashboard.json', w/'previous-version.json')
shutil.copy2(SPEC, w/'notification-contract.md')
plug = w.parent/(w.name+'-plugin')
shutil.copytree(SKILL, plug/'skills/create-dashboard')
(plug/'.claude-plugin').mkdir(parents=True)
(plug/'.claude-plugin/plugin.json').write_text(json.dumps({'name': 'gcx-dash', 'version': '0.1.0', 'description': 'gcx create-dashboard Skill'}), encoding='utf-8')

prompt = """這是本機教學用的 Grafana（只有本機，不是公司環境）。只讀寫目前目錄，不要讀父目錄。

previous-version.json 是第二版 Dashboard（UID day25-work-view-v2）。它比第一版直覺，但審查發現：拿掉了完成率；明細沒有通知編號，還多了一欄看不懂的「Value #A」；最重要的是，看完之後不知道「然後呢」：下一步要做什麼、交給誰。

請建立第三版，UID 為 day25-work-view-v3，放在資料夾 day25（folder UID：day25），標題自訂。不要修改或刪除其他 Dashboard。設計原則：
1. 由上往下三層，各回答一個問題：要不要處理？卡在哪一段？是哪幾筆？
2. 顏色只給例外；最嚴重的排前面。
3. 畫面上只用不需要翻譯的白話，不出現指標名稱、英文代碼、工程術語或看不懂的欄位。
4. 明細只在需要時才看。
5. 每一輪一顆燈號：紅＝要處理、灰＝資料不足、綠＝沒問題。
6. 每一輪一條進度條：對方確認收到 ／ 應完成。資料不足的輪次不要畫進度條，直接顯示「資料不足」。
7. 每個紅燈、灰燈旁直接寫出下一步與負責人。這兩項已經在資料裡（由人定的分派規則），請照實呈現，不要自己改寫或新增。
8. 完成率（進度條）與通知編號（明細）不能拿掉。

資料在服務 day25-work-view（Prometheus 的 job、Loki 的 service_name），請自己用 gcx 探索。通知怎樣才算完成，見 notification-contract.md。本機 Grafana 沒有截圖用的 renderer。

建好後用 gcx 實際執行每個面板的查詢確認數字，並把最後的定義存成 dashboard.json。最後用繁體中文說明：燈號、進度條、下一步各放在哪裡，看的人怎麼在幾秒內回答「然後呢」，以及還不確定的地方。"""
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
(ROOT/'latest-claude-dashboard-v3-run.txt').write_text(str(w.relative_to(ROOT)), encoding='utf-8')
print('Claude exit', p.returncode, w, 'publisher pid', pub.pid)
