## 查核結論：r2-healthy-01 → READY_FOR_REVIEW（可交人核對）

固定檢查退出碼 0，`contract_passed: true`，`approved: false`，`action_executed: false`。我沒有補送，也沒有結案。

**範圍**
- 環境：本機教學 fixture，不是正式環境。
- 版本：`delivery-hardening-local-r2`。
- 沒有連 Log server，只讀本目錄的 `task.json`、`data/`、`src/`、`design/`。
- 通知 ID 是從 `data/logs.jsonl` 的實際資料找出來的：`7e746d20853d48b9b3948c1fe92319c1`。

**依據**
1. **API 結果**
   - 來源：`data/logs.jsonl` 第 2 行，cancel 事件。
   - 內容：`result=ok`、`transitioned=true`、`refund_requested=true`，帶有該通知 ID。
   - 程式對照：`src/Program.cs` 的 cancel 路由在狀態轉換成功時才建立通知並入列。
2. **發送端觀察**（`evidence_refs`: `log:3`）
   - 來源：`data/logs.jsonl` 第 3 行，`notify_sent`。
   - 訂單、通知 ID、版本都與 task 一致。
3. **接收端佐證**（`evidence_refs`: `receipt:0`）
   - 來源：`data/receipts.json` item 0。
   - 內容：HTTP 200，payload 的 `notification_id`、`order_id`、`kind=order_cancelled`、`refund_requested=true` 都吻合。
   - 版本：`receipts.json` 沒有版本欄位，所以這筆的版本是沿用同一通知 ID 的 `notify_sent`（collect.py 標為 inherited-from-notify_sent）。
   - `receiver_status` 判為 confirmed 是因為有獨立的接收紀錄，不是只因為有 notify_sent。

**不納入的紀錄**
- `logs.jsonl` 第 4 行：`order_id=r2-shipped-01`，`rejected_shipped`，沒有通知 ID。
- 這是另一張訂單的事件，依程式邏輯也不該通知，所以我沒有混入本次判斷。
- 它的 `request_id` 和 `run_id` 與本單相同，這點只是記下來，沒有據此做任何推論。

**執行過程的修正**
- 第一次 gate 失敗（`SENDER_STATUS`）：我把 `sender_status` 寫成 `notify_sent`，但契約只允許 `confirmed` 或 `unknown`。
- 我只改了自己的 `out/result.json`，沒有動檢查器、task.json、data/ 或 scripts/，只重跑一次後通過。

**未知與限制**
- 本輪沒跑 .NET。`design/design-review.md` 第 7 點也說明，新的單元、HTTP、payload、順序重送測試都還是待執行的設計。
- 接收端是本機 FakeSink 的收據，不代表真實下游系統已處理。
- `receipts.json` 的 `at` 時間（約 1790646010.86）與 `notify_sent` 時間（09:40:10.861）相近，我沒有進一步比對時序。

**下一步（交人）**
- 核對 `out/result.json` 與上述兩筆來源。
- 若要驗證真實環境，需另行提供 Log server 的查詢入口與權限。

產出檔案：`out/result.json`、`evidence.json`（collect.py 產生）。