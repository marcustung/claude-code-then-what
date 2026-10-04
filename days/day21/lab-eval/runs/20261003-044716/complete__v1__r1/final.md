訂單 `r2-healthy-01` 的取消通知，發送端與接收端都有依據可以確認。結論已寫入 `out/result.json`。

**範圍**：這是本機教學夾具，不是正式環境。`task.json` 的版本是 `delivery-hardening-local-r2`，`data/logs.jsonl` 第 1 行的 startup 版本與它一致，而且 `faults_loaded=false`，沒有注入故障。

**查核依據**
- **API 結果**：`logs.jsonl` 第 2 行顯示 `cancel` 結果為 `ok`，`transitioned=true`，`refund_requested=true`。通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`。`src/Program.cs:105-114` 也顯示只有狀態真的轉成已取消時才會建立通知。
- **發送端**：`logs.jsonl` 第 3 行有 `notify_sent`，通知 ID、訂單 ID、request_id 都與第 2 行相同。依 `src/Program.cs:283-287`，這筆紀錄要等接收端回成功碼才會寫。
- **接收端**：`data/receipts.json` 第 0 筆是接收端的獨立收據，狀態為 200。它的內容和發送端一致：同一個通知 ID 和訂單 ID，`kind=order_cancelled`，`refund_requested=true`，`attempt=0`，也就是第一次就送達。
- **時間**：收據時間 `1790646010.8577` 換算後約為 09:40:10.858 (+08:00)，與 log 時間相符。

**其他觀察**
- 第 4 行是另一筆訂單 `r2-shipped-01`，因已出貨而被拒絕（`rejected_shipped`），沒有通知 ID。這符合設計，也沒有混入本次查核。
- 這份資料裡沒有重送、`notify_deferred`、`dead_letter` 的紀錄，也看不到重複的通知。

**缺少的來源**
- 沒有連遠端 Log server。
- 沒有 FakeSink 原始存取日誌和 `/metrics`，所以接收端只能以 `receipts.json` 為依據。
- 沒有正式環境的資料。

**下一步**：不需要補送。若要更強的佐證，可請操作者取得 FakeSink 日誌或 `/metrics`（`notify_sent_total`、`dead_letter`）來交叉比對。

我只做了查詢和分析，沒有補送也沒有結案。離線的 `collect.py` 沒有執行，是直接讀原始檔比對。