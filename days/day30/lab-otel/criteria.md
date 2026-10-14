# Day 30 OTel 實驗：Claude Code 自己的遙測，看得到什麼、看不到什麼？（2026-10-12，跑前寫定，跑後只追加）

Day 1 只提一句「也可以用 OpenTelemetry 收 Claude Code 的執行資料」；Day 30 打開公司後台，發現它能回答的只有 L1 與機器成本。本實驗在本機實際收一次 Claude Code 的 OTel 遙測，看它比後台多看到什麼、仍然看不到什麼。

## 設定

- 任務：沿用 Day 28 的通知檢查（`run.py`、`service.py`、兩支工具範本，複製自 `../day28-schedule-lab`）。唯一改動：每次 `claude -p` 加上 `OTEL_RESOURCE_ATTRIBUTES=lab.group=<組>,lab.run=<輪>`，讓遙測分得出是哪一輪。
- 跑兩組，各一次：
  - **A1**：上一輪未完又觸發、不加鎖（Day 28 結果：開了 4 張單，兩輪都說沒有重複）。
  - **C1**：不給工具權限（Day 28 結果：一張單都沒開，退出碼 0、`success`）。
- 遙測：`CLAUDE_CODE_ENABLE_TELEMETRY=1`，metrics 與 logs 以 OTLP/HTTP-JSON 送到本機 `otlp_receiver.py`（127.0.0.1:4318），原樣存成 JSONL。匯出間隔調短（metrics 5 秒、logs 2 秒）。
- **不開** `OTEL_LOG_USER_PROMPTS`、`OTEL_LOG_TOOL_DETAILS`：提示原文與工具參數不送出（預設值）。
- sonnet、`--max-budget-usd 1`；預估花費 US$0.05–0.1。
- 驗收：遙測內容以 `otel/*.jsonl` 為準；任務結果以服務端 `items.json`、`requests.jsonl` 為準。

## 事前預期

| 問題 | 預期 |
|---|---|
| 1. 看得到哪些 metrics？ | 工作階段數、花費、token、使用時間；程式碼行數、commit、PR 為 0 或不出現 |
| 2. C1 的權限拒絕看得到嗎？ | 會有 `tool_decision` 事件，決定為 reject（或等同的拒絕來源） |
| 3. A1 的重複開單看得到嗎？ | **看不到**。遙測只記 Claude 呼叫了工具，不知道開的單是否重複 |
| 4. 遙測能分辨「做了事」與「什麼都沒做」嗎？ | 可以從工具事件數間接看出（C1 沒有成功的工具結果），但沒有「任務成功／失敗」這種欄位 |
| 5. 看得到人的時間嗎？ | 只有 `active_time`（`user`／`cli`）；`claude -p` 無人打字，`user` 應為 0 或不出現 |

## 判讀界線

各組一次，示範遙測內容，不估發生率。事件名稱以實際收到的為準；若與官方文件不同，照實記錄。

## 結果（2026-10-12 03:03 UTC，`runs/20261012T030354Z/`）

任務結果與 Day 28 相同：A1 開了 4 張單（每個異常 2 張），C1 一張都沒開；三次 `claude -p` 退出碼都是 0。花費合計約 US$0.06。

| 問題 | 預期 | 實際 |
|---|---|---|
| 1. metrics | 工作階段、花費、token、使用時間；行數／commit／PR 不出現 | **符合**。每輪各有 `session.count`、`cost.usage`、`token.usage`（input／output／cacheRead／cacheCreation）、`active_time.total[cli]`。沒有 `lines_of_code`、`commit`、`pull_request` |
| 2. C1 權限拒絕 | 有 `tool_decision` reject | **符合**。C1 有一筆 `tool_decision`：Bash、`decision=reject`、`source=config`，之後沒有任何 `tool_result`。**退出碼 0 看不到的事，遙測看得到** |
| 3. A1 重複開單 | 看不到 | **符合**。A1 兩輪各有一筆約 40 秒的 Bash `tool_result`，`success=true`。兩輪時間重疊，但遙測沒有任何欄位標出重複；要靠服務端紀錄 |
| 4. 做了事 vs 沒做 | 只能從工具事件間接看 | **符合**。A1 每輪 2 次 accept＋2 次成功的工具結果；C1 1 次 reject、0 次工具結果。沒有「任務成功」欄位 |
| 5. 人的時間 | `user` 為 0 或不出現 | **符合**。只有 `active_time[cli]`（A1 約 51 秒、C1 約 7 秒），沒有 `user` |

### 判準沒涵蓋的觀察

- **提示與回覆預設遮掉**：`user_prompt` 的 `prompt`／`prompt_text`、`assistant_response` 的 `response` 都是 `<REDACTED>`，只留長度。
- **但每一筆事件都帶身分**：`user.email`、`user.account_id`、`organization.id`、`session.id`。遙測是個人資料，收進公司觀測平台前要決定誰能看、保存多久。公開版已把這些欄位與外掛名稱改成 `<REDACTED>`；原始檔只留在本機 `reviews/day30-otel-raw/`。
- **環境也會被記下**：`plugin_loaded` 事件列出載入的外掛名稱與是否含 hook、MCP；`managed_settings_resolved` 記下受管設定的來源。
- `api_request` 有模型、每次請求花費、延遲、首字時間（`ttft_ms`），可以算出每一輪、每個模型的成本。
- `tool_decision` 的 `source=config` 表示由設定檔（`--allowedTools`）決定，不是人按的；在有人值守的工作階段，這個欄位可以分辨「人核准」與「規則放行」。
