"""Day 25 round 6: user's reference layout (big result cards on top, details below); builds day25-work-view-v6.
Reconciled data is published by publish_to_grafana.py (looped in the background during the run)."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
SPEC = ROOT.parent/'order-cancel-lifecycle/specs/notification-contract-v2.1.md'
SKILL = Path.home()/'.claude/skills/create-dashboard'
EDITOR_CFG = os.path.join(os.environ['TEMP'], 'day25-gcx-editor.yaml')

w = ROOT/'runs-claude-dashboard'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-v6'); w.mkdir(parents=True)
first = ROOT/(ROOT/'latest-claude-dashboard-v5-run.txt').read_text().strip()
shutil.copy2(ROOT/'user-reference-layout.webp', w/'user-reference-layout.webp')
shutil.copy2(first/'dashboard.json', w/'previous-version.json')
shutil.copy2(SPEC, w/'notification-contract.md')
plug = w.parent/(w.name+'-plugin')
shutil.copytree(SKILL, plug/'skills/create-dashboard')
(plug/'.claude-plugin').mkdir(parents=True)
(plug/'.claude-plugin/plugin.json').write_text(json.dumps({'name': 'gcx-dash', 'version': '0.1.0', 'description': 'gcx create-dashboard Skill'}), encoding='utf-8')

prompt = """這是本機教學用的 Grafana（只有本機，不是公司環境）。只讀寫目前目錄，不要讀父目錄。

previous-version.json 是第五版 Dashboard（UID day25-work-view-v5）。使用者給了一張參考圖 user-reference-layout.webp（請先打開看），原話：「我想要類似這樣簡單的結果，上方是簡單結果，下方是詳細資料，ex：卡在哪」。參考圖的重點：上方幾張大卡片，每張只回答一件事，一個大字結論加一行小字；細節在下方。

使用者另外指出：「取消通知應該只是環節的一部分」「要監控是否應該看全部的流程？」所以這一版的主問題改成整件事：**取消的訂單都處理完了嗎？** 通知只是流程中的一段。依規格 notification-contract.md 的 NC-04，「API 接受」≠「狀態已改」≠「通知送達」。

完整流程共八段（資料 flow_stage_info 有每段是否有資料與說明；1–6 段的筆數在 flow_count）：
收到請求 → 取消成功 → 提出退款 → 排進待送 → 系統說已送 → 對方收到 → 待處理清單（無資料）→ 退款完成（無資料）
沒有資料的段落要照實顯示「無資料」與資料裡的說明，不能畫成綠燈，也不能省略不畫。
request_outcome 是取消請求的結果：取消成功、被拒（已出貨）、重複取消、無效請求、系統錯誤；被拒與重複取消是業務規則的正常結果，不算問題。

第五版審查另外發現：「卡在哪」一行塞太多欄出現橫向捲軸、資料時間被切掉；「哪幾筆」少了通知編號。

請建立第六版，UID day25-work-view-v6，資料夾 day25（folder UID：day25），預設時間範圍最近 5 分鐘。不要修改或刪除其他 Dashboard。設計稿（使用者同意的方向，面板與查詢由你決定）：

    取消的訂單都處理完了嗎？
    上方：大卡片，大字只放結論，下面一行小字
      狀態        ✗ 沒處理完       小字：卡在哪一段、哪一項
      取消成功     ✓ 全部           小字：被拒、重複取消另計（業務規則）
      客人被告知   33%              小字：漏送通知 對方收到 3／9
      退款         ? 無資料          小字：沒有監控
    下方：詳細資料，只列有問題的項目
      卡在哪？完整流程每段一格：✓ 有資料且正常；✗ 卡住（紅）；? 無資料（灰）
      漏送通知的補充：6 筆停在「延後」，之後沒有再送；其中 3 筆是退款通知
      回得慢・資料未齊：紀錄不全，沒有通知編號，也沒有結束紀錄
      誰處理？只列有問題的項目（owner、next_step 照資料）
      ▸ 哪幾筆？（收合；訂單、通知編號、退款、最後一步、等了多久，退款排前面）

原則：
- 主標題就是上面那個問題；上方卡片是答案，下方是證據。
- 不能有任何捲軸（直向或橫向）；放不下就換行或拆開。
- 文字簡短，照資料顯示，不用「批」「輪」與術語；紅＝有問題、灰＝無資料或紀錄不全、綠＝正常。
- 進度與通知編號都要在。

其他資料：work_status（status_text、stuck_detail、data_time、next_step、owner、scenario）、work_expected、work_matched、work_refund_unmatched；Loki 事件有 refund、last_step、cancel_time、waited、notification_id。請自己用 gcx 探索。本機 Grafana 沒有截圖用的 renderer。
環境限制：允許清單一次只認一個 gcx 指令，不要用 ;、&&、| 串接。gcx 已經設定好連線，**gcx config 不開放**（可能印出憑證），不需要檢查設定。可用的子命令：
gcx datasources list／get／prometheus …／loki …、gcx metrics query／labels／metadata、gcx logs query／labels／series、gcx resources validate／push／get／pull／list-types／list-examples、gcx dashboards get／list／search／create／update、gcx agent skills get。

建好後用 gcx 實際執行每個面板的查詢確認數字，把最後的定義存成 dashboard.json。最後用繁體中文說明：上方每張卡片回答什麼、流程八段怎麼呈現、怎麼避免捲軸。"""
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
(ROOT/'latest-claude-dashboard-v6-run.txt').write_text(str(w.relative_to(ROOT)), encoding='utf-8')
print('Claude exit', p.returncode, w, 'publisher pid', pub.pid)
