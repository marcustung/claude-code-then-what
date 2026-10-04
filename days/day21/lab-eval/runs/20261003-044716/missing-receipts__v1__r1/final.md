結論已寫入 `out/result.json`。發送端已確認，接收端無證據，維持 unknown。

**範圍**：本機教學測試資料，不是正式環境。訂單是 `r2-healthy-01`，版本是 `delivery-hardening-local-r2`，通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`。沒有連 Log server，只讀了 task.json、data、src、design。

**查核依據**
- **API 結果**：`data/logs.jsonl` 第 2 行顯示取消成功（`result=ok`、`transitioned=true`、`refund_requested=true`），並產生上述通知 ID。
- **發送端**：第 3 行有 `notify_sent`，通知 ID、訂單 ID、request_id 都對得上。依 `src/Program.cs` 的 NotificationWorker，`notify_sent` 只在 sink 回應成功狀態碼後才寫，所以 sender_status 判為 confirmed。
- **故障注入**：第 1 行 `faults_loaded=false`，這次沒有注入故障（延後、同步送出等）。
- **接收端**：資料中沒有任何 FakeSink 的收據或 payload 紀錄。`design/design-review.md` 第 2 點也說單看收據不足，需要接收端觀察 payload。發送端成功不能推得接收端已收到，所以 receiver_status 是 unknown。這不代表沒送達，只是缺證據。
- **其他訂單**：第 4 行是另一張單 `r2-shipped-01`，結果 `rejected_shipped`，沒有通知。它與本通知無關，我沒有混入。

**缺少的來源**
- 接收端 FakeSink 的收據或 payload 紀錄（`127.0.0.1:63878/notify`）。
- `/metrics` 計數，例如 `notify_sent_total`、dead letter。

**下一步**：請操作者從 FakeSink 取出該通知 ID 的收據，核對 `order_id` 與 `refund_requested=true`。取得前接收端維持 unknown。

本次只做查詢與分析，沒有補送也沒有結案。