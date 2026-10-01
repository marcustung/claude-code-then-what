# 查核結果：無法完成，接收端維持 unknown

Log 查詢失敗兩次，所以沒有任何 Log 證據。我沒有改用其他資料源，也沒有查其他事件。

## 1. 任務範圍（來源：`task.json`）
- order_id：`live-20261001-02-query-failure`，版本：`delivery-hardening-local-r2`，環境：local Docker teaching lab。
- 時間窗：`2026-09-30T19:26:25.016660Z` 到 `2026-09-30T19:26:26.247363Z`。
- datasource_uid：`day17-unavailable`，標籤：`lab_case="query-failure"`。
- 服務：order-api、notification-receiver。

## 2. 程式與設計核對（已讀原件）
- **API 建通知與入列**（`src/Program.cs:79-89`）：只有狀態真的從未取消變成已取消時，才建立 `notification_id`（GUID）。預設路徑寫入 Channel，`SyncNotify` 演練開啟時改為同步送出。
- **API 日誌**（`Program.cs:92`）：`cancel` 事件帶有 `order_id` 和 `notification_id`，所以 order_id 是找 notification_id 的入口。
- **背景 Worker**（`Program.cs:225-268`）：POST 到 sink，失敗重試 3 次。成功才寫 `notify_sent`，失敗則寫 `notify_dead_letter`。
- **`notify_sent` 的含意**：它只代表發送端收到 sink 回應成功（`IsSuccessStatusCode`），不等於接收端已核對。
- **設計文件**（`design/design-review.md`）：第 1 點說明 Worker 送達與 HTTP 回應沒有固定先後。第 7 點說明本輪未跑 .NET。
- 程式碼與設計中沒有 notification-receiver 的實作，接收端證據只能來自 Log。

## 3. Log 查詢紀錄
| # | 工具與資料源 | 查詢條件 | 結果 |
|---|---|---|---|
| 1 | `query_loki_logs`，`day17-unavailable` | `{lab_case="query-failure"} \|= "live-20261001-02-query-failure"`，起訖用 task.json 原值（6 位微秒），forward，limit 100 | 工具錯誤：`parsing start time: syntax error: unexpected tDIGIT at character 25`。這是時間格式錯誤，查詢沒有執行。 |
| 2 | 同上 | 同條件，時間改為 `19:26:25.016Z` 到 `19:26:26.248Z`（毫秒，外擴不到 1 ms，不改變事件範圍） | 工具錯誤：`loki API returned status code 502`（內容為空）。 |

因為資料源回 502，查詢 #2 也沒有執行成功。這不是「查詢成功但無符合資料」，不能據此判定通知未送達。

## 4. 各層狀態
- **API 結果**：unknown。沒有 `cancel` 日誌，看不到 HTTP 狀態，也看不到 `transitioned`。
- **發送端觀察**：unknown。沒有 `notify_sent`、`notify_dead_letter` 或 `notify_attempt_failed`，也取不到 notification_id。
- **接收端佐證**：unknown。沒有 notification-receiver 的任何紀錄。

## 5. 缺少的來源與下一步
缺少的來源：
- `day17-unavailable` 中 order-api 與 notification-receiver 的 Log。
- 透過 order_id 取得的 notification_id。

下一步（建議由操作者或有權限者執行）：
1. 確認 Grafana 與 Loki 的 `day17-unavailable` 資料源狀態。可用 `check_datasources_health` 檢查同一個 UID，並查看 Grafana 到 Loki 的 502 原因。
2. 恢復後重跑查詢 #2，先用 order_id 找 `cancel` 日誌中的 notification_id，再用該 ID 查 notification-receiver 的收據。
3. 若資料源確定無法恢復，請提供正確的 UID 或新的授權範圍。我不會自行切換資料源。

我沒有補送、沒有結案，也沒有修改任何檔案。

```json
{
  "order_id": "live-20261001-02-query-failure",
  "sender_status": "unknown",
  "receiver_status": "unknown",
  "missing_sources": [
    "day17-unavailable: order-api logs (Loki 502, query not executed)",
    "day17-unavailable: notification-receiver logs",
    "notification_id (not obtainable without order-api log)"
  ],
  "next_action": "Restore or check the day17-unavailable datasource (Grafana/Loki 502), then rerun the order_id query to get notification_id and check the receiver logs. Do not switch datasources, resend, or close the case."
}
```