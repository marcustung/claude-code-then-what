## 查核結果：READY_FOR_REVIEW，可交人核對

固定檢查已執行：`gate.py` 回傳 `contract_passed: true`、`errors` 為空、`approved: false`、`action_executed: false`。我沒有補送，也沒有結案。

**範圍**
- 訂單是 `r2-healthy-01`，版本是 `delivery-hardening-local-r2`。
- 環境是本機教學 fixture，不是正式環境。
- 沒有連 Log server，只用 `data/`、`src/`、`design/` 三處資料。
- `collect.py` 沒有回報缺來源或格式錯誤：`logs.jsonl` 和 `receipts.json` 都在，也都能解析。

**依據**
1. **程式與設計**
   - 取消 API 在狀態真的轉成已取消時才建立通知，並在回應前入列（`src/Program.cs`，設計文件第 1 點）。
   - 已出貨（409）和重複取消（idempotent）都不通知。
   - 實際送達由背景 Worker 負責，和 HTTP 回應沒有固定先後。
2. **發送端（confirmed）**
   - `data/logs.jsonl` 第 2 行：`cancel` 結果 `ok`，`transitioned=true`，`refund_requested=true`。
   - 第 3 行：`notify_sent`，通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`，版本與 `task.json` 一致。
   - 對應 ref 是 `log:3`。
3. **接收端（confirmed）**
   - `data/receipts.json` item 0：status 200，`order_id`、`notification_id`、`request_id` 與發送端一致。
   - `kind` 是 `order_cancelled`，`refund_requested` 是 true，`attempt` 是 0。
   - 對應 ref 是 `receipt:0`。
4. **對照**
   - 日誌時間 09:40:10.861，收據 epoch 1790646010.858 換算後約同一秒，順序合理。
   - 只有一筆通知 ID，沒有重複送。
5. **旁證**
   - 日誌第 4 行是另一張單 `r2-shipped-01`，結果 `rejected_shipped`，`notification_id` 為 null。
   - 這符合「已出貨不通知」，且與本訂單分開，沒有混用。

**Unknown 與限制**
- **接收端版本沒有獨立來源**：`receipts.json` 沒有版本欄位，`collect.py` 是沿用同一通知 ID 的 `notify_sent` 版本（`version_source=inherited-from-notify_sent`）。所以「接收端跑的是哪個版本」是推定，不是獨立佐證。
- **接收端是 FakeSink 的本機收據**：設計文件第 2 點說明，單看收據不足以證明 payload 完整。例如 FakeSink 未保存的欄位，不能由此推論 payload 沒變。
- **沒有跑 .NET**：設計文件第 7 點說明新增的測試仍是待執行設計。本次只做靜態讀程式與資料比對，沒有重現執行。
- **範圍有限**：這只證明本機 fixture 的單一事件。不能外推到正式環境的送達率，也不能外推到並行取消（設計文件第 4 點：read/decide/write 非整體原子）。

**下一步**
- 交人核對 `out/result.json`。
- 若要把接收端版本補成獨立佐證，需要在 FakeSink 收據加版本欄位，或取得接收端自己的日誌。這屬於變更，我沒有做。

**輸出檔**
- `out/result.json`：`sender_status` 和 `receiver_status` 皆為 `confirmed`，`evidence_refs` 是 `["log:3","receipt:0"]`，`missing_sources` 為空。
- `collect.py` 另外寫了 `evidence.json`。