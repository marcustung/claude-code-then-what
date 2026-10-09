"""Day 25 round 7: one-sentence status, plain words, flow without the self-reported stage, and the AI investigation card; builds day25-work-view-v7.
Reconciled data is published by publish_to_grafana.py (looped in the background during the run)."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
SKILL = Path.home()/'.claude/skills/create-dashboard'
EDITOR_CFG = os.path.join(os.environ['TEMP'], 'day25-gcx-editor.yaml')

w = ROOT/'runs-claude-dashboard'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-v7'); w.mkdir(parents=True)
first = ROOT/(ROOT/'latest-claude-dashboard-v6-run.txt').read_text().strip()
shutil.copy2(ROOT/'user-reference-layout.webp', w/'user-reference-layout.webp')
shutil.copy2(first/'dashboard.json', w/'previous-version.json')
shutil.copy2(SPEC, w/'notification-contract.md')
plug = w.parent/(w.name+'-plugin')
shutil.copytree(SKILL, plug/'skills/create-dashboard')
(plug/'.claude-plugin').mkdir(parents=True)
(plug/'.claude-plugin/plugin.json').write_text(json.dumps({'name': 'gcx-dash', 'version': '0.1.0', 'description': 'gcx create-dashboard Skill'}), encoding='utf-8')

prompt = """這是本機教學用的 Grafana（只有本機，不是公司環境）。只讀寫目前目錄，不要讀父目錄。

previous-version.json 是第六版 Dashboard（UID day25-work-view-v6），版面（上方大卡片、下方細節，參考圖 user-reference-layout.webp）使用者認可。使用者驗收第六版的意見：
- 「? 無資料 是什麼」「系統說已送 是什麼」：看不懂。
- 「一句話說目前狀態是什麼」：缺一句話的結論。
- 「檢查 dashboard 目的是否目前有回答」：主問題「取消的訂單都處理完了嗎？」只回答了一半，小字寫的是情境名稱（例如「漏送通知」），看不出影響到誰。
- 使用者另外要求加一個「AI 判斷」欄位，示範 LLM 怎麼幫值班的人想下一步。

請建立第七版，UID day25-work-view-v7，資料夾 day25（folder UID：day25），預設時間範圍最近 5 分鐘，沿用第六版版面，改這些地方：
1. 最上方放一句話結論與下一步：照資料 work_summary 的 summary 與 next 兩個標籤原樣顯示（固定規則產生的，不要改寫）。
2. 「無資料」全部改成「看不到」，並在旁邊照資料顯示原因（flow_stage_info 的 note）。
3. 流程拿掉「系統說已送」。流程現在是 flow_count／flow_stage_info 的七段：收到請求 → 取消成功 → 提出退款 → 排進待送 → 對方收到 → 待處理清單（看不到）→ 退款完成（看不到）。系統自報的已送出數（sender_reported_sent）若要出現，只能放在證據裡，和對方收到並列（例如「系統記錄已送 9，對方只收到 3」），不能當成一段流程或標綠燈。
4. 卡片小字講影響，不講情境名稱：照 work_status 的 impact 標籤顯示（例如「6 位客人沒收到通知（3 位是退款）」）。
5. 新增「AI 判斷，待確認」區塊：資料 work_ai_card（每個有問題的項目一筆：question、answer、verified、first_step、generated_at）。必須清楚標示「AI 判斷，待確認」，和規則判定的狀態、負責人分開，不能改變燈號；文字照資料顯示。

其他原則照舊：不能有任何捲軸；文字簡短；不用「批」「輪」與術語；紅＝有問題、灰＝看不到或紀錄不全、綠＝正常；進度與通知編號都要在。

資料：work_summary、work_status（status_text、impact、stuck_detail、data_time、next_step、owner、scenario）、flow_count、flow_stage_info、request_outcome、work_expected、work_matched、work_refund_unmatched、sender_reported_sent、work_ai_card；Loki 的 service_name="day25-work-view" 事件有 refund、last_step、cancel_time、waited、notification_id。本機 Grafana 沒有截圖用的 renderer。
環境限制：允許清單一次只認一個 gcx 指令，不要用 ;、&&、| 串接。gcx 已經設定好連線，**gcx config 不開放**，不需要檢查設定。可用的子命令：
gcx datasources list／get／prometheus …／loki …、gcx metrics query／labels／metadata、gcx logs query／labels／series、gcx resources validate／push／get／pull／list-types／list-examples、gcx dashboards get／list／search／create／update、gcx agent skills get。

建好後用 gcx 實際執行每個面板的查詢確認數字，把最後的定義存成 dashboard.json。最後用繁體中文說明：結論句放哪、看不到怎麼呈現、AI 判斷怎麼和規則分開。"""
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
(ROOT/'latest-claude-dashboard-v7-run.txt').write_text(str(w.relative_to(ROOT)), encoding='utf-8')
print('Claude exit', p.returncode, w, 'publisher pid', pub.pid)
