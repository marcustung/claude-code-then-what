# Day 25：看著 Dashboard，要怎麼知道訂單卡在哪？

這個教學包保存 Day 25 三層實跑的程式、結果與判準。每一層都由 Claude Code 動手，再用事前寫好的檢查抓「看起來對、其實不對」的地方。

| 層 | 問的問題 | Claude Code 做什麼 | 看哪裡 |
|---|---|---|---|
| 一 | 數字對了嗎？ | 只看通知契約與原始紀錄，寫逐筆核對程式 `reconcile.py` | `runs-claude/`：兩輪的 `reconcile.py`、`grading.json`（八項檢查）、`answer.md`、`trace-summary.txt` |
| 二 | 看完知道做什麼嗎？ | 用 gcx 在本機 Grafana 建 Dashboard，依驗收原話逐版修改 | `runs-claude-dashboard/`：15 次執行各自的 `prompt.txt`、`answer.md`、`dashboard.json`、截圖；判準與驗收原話在 `claude-dashboard-*.md` |
| 三 | 第一步查哪裡？ | 照規則選定的題目，用 Day 24 的唯讀 MCP 查證，產出調查卡 | `runs-ai-card/`：每輪的提示、`stdout.json`、`tool-audit.summary.jsonl`；判準在 `ai-hint-criteria.md`、`ai-card-criteria.md`、`ai-card-plain-criteria.md` |

## 不用重跑，就能核對的東西

需要 Python 3（標準函式庫）。

- **逐筆核對的結果**：`runs/` 下三次 `build.py` 的輸出，`view.json` 是每一筆取消對到哪張收據、`checks.json` 是八項檢查。`grafana-publish-rows.json` 是送進 Grafana 的彙總。
- **調查卡白話檢查**：`python check_ai_card_plain.py runs-ai-card/20261009T005823Z-plain2/ai-cards.json`，會列出 Dashboard 顯示的欄位有沒有英文、字數，以及卡片上的查詢是否在稽核摘要裡找得到。
- **Dashboard 各版差異**：比較 `runs-claude-dashboard/*/dashboard.json`；`check_v7fix2.py` 是定版前的預檢（沒有打勾叉叉、面板與查詢不變），需要本機 Grafana 才能執行。

## 這個公開版拿掉了什麼

原始紀錄（服務 Log、對方收據、請求紀錄）不隨本篇公開。所以：

- `runs-claude/*/data/`、`_grading/`（改造案例）與 `trace.jsonl` 不在這裡；`trace-summary.txt` 只保留回合、費用與工具呼叫清單。
- 調查卡的 `tool-audit.jsonl` 會包含查回來的原始紀錄，改放 `tool-audit.summary.jsonl`：每次查詢的指令、結束碼與筆數。
- 建 Dashboard 時給 Claude 看的參考版面圖，以及每次執行複製的 Skill 副本，也不在這裡。

因此 `build.py`、`publish_to_grafana.py`、`ai_card.py` 在這個目錄裡讀不到原始紀錄，無法直接重跑；程式本身照原樣保留，供閱讀判準與流程。

## 重跑需要的環境（原始紀錄公開後）

- `publish_to_grafana.py`：把核對結果與原始紀錄送進 Day 24 的本機 Grafana（OTLP `127.0.0.1:4324`）；`--loop 30` 每 30 秒重送一次指標。
- `run-claude-dashboard*.py`：用 `claude -p` 搭配 gcx 建 Dashboard。允許清單逐一列出 gcx 子命令，`gcx config` 不開放；Editor 帳號只開一個資料夾。
- `ai_card.py`：用 `claude -p --tools ""`，只給 Day 24 的唯讀 MCP（`days/day24/lab-observability/gcx_readonly_mcp.py`），`--json-schema` 固定輸出；每次查詢寫進稽核檔。

## 資料界線

- 教學紀錄重放，跑在本機 Grafana，不是 Production。
- 每次都只用 sonnet 跑一次，不代表穩定度；沒有量測人工節省時間。
- Dashboard 的驗收人只有作者本人，還沒找值班同仁只看截圖實測。
- 偏離紀錄（指令被允許清單擋下、殘留舊指標、表格高度估錯等）都照實留在判準檔，沒有刪除。
