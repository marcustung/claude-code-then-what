# 通知查核：live-20261001-02-missing-receipts

**結論：** 發送端有記錄，接收端查無佐證，所以接收端狀態是 unknown。這不代表一定沒送達。

## 1. 程式與設計（唯讀）
- 版本：task.json 為 `delivery-hardening-local-r2`，與 API log 的 `version` 欄位一致。
- `src/Program.cs:49-94`：取消成功後建立通知（行 82）並寫入 Channel（行 88）。Log 寫在行 92，回應在行 93。
- `src/Program.cs:257-261`：worker 收到 HTTP 2xx 才寫 `notify_sent`。所以 `notify_sent` 只代表 sink 回了成功狀態，不是接收端 log 的核對。
- `design/design-review.md` 第 2 點與第 7 點：單看收據不足以判斷 payload，且本輪沒有跑過 .NET。
- 行號以本次讀到的檔案為準。

## 2. 查詢紀錄
datasource 都是 `day17-loki`。

| # | 條件 | 結果 |
|---|---|---|
| Q1 | `list_loki_label_names` | 權限未授權，沒有執行，也沒有重試 |
| Q2 | `{lab_case="missing-receipts"} \|= "<order_id>"`，時間窗 19:26:23Z–19:26:25Z | 回傳 2 行，都來自 order-api，掃描 3 行 |
| Q3 | `{lab_case="missing-receipts", service_name="notification-receiver"} \|= "<notification_id>"`，同時間窗 | 0 行，掃描 0 行 |
| Q4 | `query_loki_stats`（receiver 串流） | 權限未授權，沒有執行 |
| Q5 | `{lab_case="missing-receipts"} \|= "<notification_id>"`，不限服務，同時間窗 | 只回傳 Q2 那 2 行，receiver 沒有 |

第一次查詢因時間字串精度過細而格式錯誤。我改用整秒，範圍是 19:26:23Z 到 19:26:25Z，比 task.json 時間窗稍寬。

## 3. 結果分層
- **API 結果（order-api，`cancel` 事件）：**
  - `order_id` 與 `request_id` 都是 `live-20261001-02-missing-receipts`。
  - `result=ok`，`transitioned=true`，`refund_requested=true`，`queue_depth=0`。
  - 通知 ID 是 `bda1a73ba5f84cb1abcc6d0f265e1e95`。
  - 時間是 2026-10-01T03:26:24.4355+08:00。
  - 來源是 `/logs/missing-receipts/api/logs.jsonl`。
- **發送端觀察（order-api，`notify_sent` 事件）：**
  - 同一個 `notification_id`，時間 03:26:24.4727+08:00，約在 API 事件後 37 ms。
  - 沒有 `notify_attempt_failed`、`notify_deferred` 或 `notify_dead_letter`。
  - 這些沒有出現，是在 Q2 和 Q5 的結果中沒看到，不是另外查過。
- **接收端佐證：** Q3 無符合資料，Q5 也沒有 receiver 的行，所以沒有佐證。

## 4. 未知與限制
- Q3 掃描 0 行。這可能是 receiver 串流在此時間窗沒有資料，也可能是 receiver 的 label 值與我用的 `service_name="notification-receiver"` 不同。因為 Q1 和 Q4 沒被授權，我無法分辨是哪一種。
- Q5 沒帶服務 label，也沒看到 receiver 的行，但這只說明 lab_case 下沒有含該 ID 的 receiver log。如果 receiver 只記 `order_id` 而不記 `notification_id`，Q5 會漏掉。Q2 已用 `order_id` 查過，也只有 order-api 的行，不過 Q2 同樣受限於 receiver 的 label 是否真的歸在此 lab_case。
- 不能由 `notify_sent` 推出接收端已收到，也不能由查不到推出未送達。

## 5. 下一步（最小補查）
1. 請操作者授權 `list_loki_label_values`（`service_name`）或 `list_loki_label_names`，確認 receiver 在此 lab_case 下的實際 label。
2. 用正確 label 重查同一時間窗，同時用 `notification_id` 和 `order_id` 比對。
3. 若 receiver 確實沒有資料，再請負責人確認 receiver 的 log 是否有進 Loki。
4. 我沒有補送、沒有結案，也沒有查其他資料來源。

```json
{
  "order_id": "live-20261001-02-missing-receipts",
  "sender_status": "notify_sent observed in order-api log (notification_id bda1a73ba5f84cb1abcc6d0f265e1e95, 2026-10-01T03:26:24.4727+08:00); no failed/deferred/dead_letter events seen",
  "receiver_status": "unknown",
  "missing_sources": [
    "notification-receiver log entries for notification_id bda1a73ba5f84cb1abcc6d0f265e1e95 (Q3 and Q5 returned no receiver rows)",
    "label inventory for day17-loki (list_loki_label_names not permitted)",
    "query_loki_stats for the receiver stream (not permitted)"
  ],
  "next_action": "Get list_loki_label_values/list_loki_label_names authorized, confirm the receiver's actual service_name under lab_case=missing-receipts, then re-query the same time window by notification_id and order_id. Do not resend or close until the receiver evidence is confirmed."
}
```