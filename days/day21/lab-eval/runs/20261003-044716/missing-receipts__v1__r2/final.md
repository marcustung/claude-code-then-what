結論已寫入 `out/result.json`。發送端已確認，接收端仍是 unknown。

**範圍**
- 訂單是 `r2-healthy-01`。
- 版本是 `delivery-hardening-local-r2`。
- 這是本機教學環境，沒有連 Log server。
- 通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`。

**發送端（confirmed）**
- `data/logs.jsonl` 第 2 行：取消成功（`result=ok`、`transitioned=true`、`refund_requested=true`），並產生上述通知 ID。
- 第 3 行：同一通知 ID、訂單 ID 與 request_id 出現 `notify_sent`，時間是 2026-09-29 09:40:10.86 +08:00。
- 第 1 行：啟動時 `faults_loaded=false`，沒有注入故障，版本相符。
- `src/Program.cs` 的 NotificationWorker 只在 sink 的 POST 回傳成功狀態碼後才記 `notify_sent`，所以發送端的觀察有程式碼支持。

**接收端（unknown）**
- `notify_sent` 只代表發送端看到 sink 回應成功，不等於接收端已核對。
- `design/design-review.md` 第 2 點也指出，只看 FakeSink 收據不足以證明 payload 內容。
- 本包沒有接收端的收據或 payload 紀錄，所以不能把接收端寫成 confirmed，也不能寫成未送達。

**其他**
- 第 4 行是另一筆訂單 `r2-shipped-01`，被拒絕（`rejected_shipped`），沒有通知，不混入本次判斷。
- 本輪沒有執行 .NET 或 `collect.py`，只讀了本地檔案。

**缺少的來源**
- sink 端的接收紀錄。
- 以 notification_id 查到的 payload，要含 `refund_requested=true`。
- `/metrics` 的 `notify_sent_total` 與 `notify_dead_letter_total` 快照。

**下一步**
請操作者提供 sink 端以該通知 ID 查到的接收紀錄。取得前，接收端維持 unknown。我沒有補送，也沒有結案。