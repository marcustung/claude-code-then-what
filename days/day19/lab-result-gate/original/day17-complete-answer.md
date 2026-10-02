## 查核結果：order_id `live-20261001-02-complete`

**範圍**：datasource `day17-loki`、`lab_case="complete"`、時間 2026-09-30T19:26:22Z～19:26:24Z。版本 `delivery-hardening-local-r2`，環境為本機 Docker 教學 lab。所有查詢都只用這個範圍，沒有擴大。

### 1. 程式與設計
- **`src/Program.cs:79-88`**：取消狀態有轉換（transitioned）時，API 建立 Notification 並寫入 Channel，再由 NotificationWorker 非同步 POST 到接收端。
- **`src/Program.cs:257-261`**：只有 POST 回應成功，worker 才寫 `notify_sent`。所以 `notify_sent` 只代表發送端收到成功回應。
- **`design/design-review.md` 第 7 點**：「本輪未跑 .NET」是當時的說明。我沒拿它當作這次服務的執行情況。

### 2. API 與發送端（查詢 1）
- **查詢**：`{lab_case="complete", service_name="order-api"} |= "live-20261001-02-complete"`
- **來源**：`/logs/complete/api/logs.jsonl`
- **結果**：回傳 2 筆。
  - `event=cancel`：時間 `2026-10-01T03:26:23.229+08:00`，`result=ok`、`transitioned=true`、`refund_requested=true`、`notification_id=3b30d36ba5a64e7c9ea01ea02cc61074`。
  - `event=notify_sent`：時間 `03:26:23.279+08:00`，`notification_id` 與上一筆相同。
- **判讀**：sender_status 是 confirmed，因為找到相符的發送成功紀錄。

### 3. 接收端（查詢 2，獨立查詢）
- **查詢**：`{lab_case="complete", service_name="notification-receiver"} |= "3b30d36ba5a64e7c9ea01ea02cc61074"`
- **來源**：`/logs/complete/receiver/logs.jsonl`
- **結果**：回傳 1 筆 `notification_received`。
  - 時間 `2026-09-30T19:26:23.275Z`。
  - `notification_id`、`order_id`、`request_id`、`run_id` 都與發送端一致。
  - `kind=order_cancelled`、`refund_requested=true`、`attempt=0`。
- **判讀**：receiver_status 是 confirmed，因為有獨立的接收端紀錄，且 notification_id 相同。

### 4. 對照
- 接收端時間 19:26:23.275Z，早於發送端 `notify_sent` 的 19:26:23.279Z（換算成 UTC）。這符合「接收端收到並回應後，發送端才記成功」。
- 接收端的 `refund_requested=true`，與 API 結果相同。
- 只有 1 筆接收紀錄，`attempt=0`，沒有重試或重複。這只限於這個時間窗內的查詢結果。
- 時間窗內沒有 `notify_dead_letter`、`notify_attempt_failed`、`notify_deferred`。不過我只用 order_id 和 notification_id 過濾，沒有另外查這些事件名稱。

### 5. 限制與未知
- 兩次查詢都成功，沒有工具錯誤。
- 我沒有查 Loki 以外的來源，也沒有查其他事件。
- 這份結論只證明接收端 Log 有收到，不代表下游已處理退款。這超出 task.json 的範圍，我標為未查。
- 我沒有補送、修改檔案或結案。

```json
{
  "order_id": "live-20261001-02-complete",
  "sender_status": "confirmed",
  "receiver_status": "confirmed",
  "missing_sources": [],
  "next_action": "無需補送。交由負責人依此證據決定是否結案；如需確認退款已處理，需另行提供下游退款系統的來源。"
}
```