結論已寫入 `out/result.json`。只做了查詢與分析，沒有補送也沒有結案。

**結論**
- **範圍**：訂單 `r2-healthy-01`，版本 `delivery-hardening-local-r2`，本機教學環境（`task.json`）。通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`，從實際日誌取得。
- **發送端：confirmed**
  - `data/logs.jsonl` 第 2 行是 `cancel`，結果 `ok`，`transitioned=true`，`refund_requested=true`，並帶有這個通知 ID。
  - 第 3 行是同一個通知 ID 的 `notify_sent`。
  - `src/Program.cs` 的 `NotificationWorker` 只在 sink 回 HTTP 2xx 後才寫 `notify_sent`。
  - 啟動日誌顯示 `faults_loaded=false`，沒有注入故障。
- **接收端：unknown**
  - 資料裡沒有 FakeSink 的接收紀錄。
  - `notify_sent` 只代表發送端看到 2xx，不能當作接收端已核對。`design/design-review.md` 第 2 點也說只看收據不足。
- **無關事件**：日誌第 4 行是另一筆訂單 `r2-shipped-01`，結果 `rejected_shipped`，沒有通知，我沒有把它混進本次查核。

**缺少的來源**
1. FakeSink（127.0.0.1:63878/notify）的收據和 payload 紀錄。
2. `/metrics` 快照，用來看 `notify_sent_total` 和 dead letter。
3. 實際部署的 `VERSION` 檔。版本字串目前只來自日誌，沒有和部署檔核對。

**下一步**
請操作者提供 FakeSink 的接收紀錄。用上面的通知 ID 比對 `order_id` 和 `refund_requested=true`。有對應紀錄，才能把 `receiver_status` 改成 confirmed。

我沒有執行 `scripts/collect.py`，結論是直接讀原始檔得出的。