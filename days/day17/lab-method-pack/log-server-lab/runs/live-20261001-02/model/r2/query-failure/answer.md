## 查核結果：Log 查詢失敗，無法確認通知

**結論：** `day17-unavailable` 這個資料來源連續兩次回 HTTP 502，所以拿不到任何 Log。我找不到 notification_id，也沒辦法查接收端。發送端和接收端都標為 unknown。這不代表通知沒送到。

### 1. 任務範圍（來源：`task.json`）
- order_id：`live-20261001-02-query-failure`
- 版本：`delivery-hardening-local-r2`，環境為本機 Docker 教學實驗室。
- 時間窗：`2026-09-30T19:26:25Z` 到 `19:26:27Z`
- datasource_uid：`day17-unavailable`，lab_case：`query-failure`
- 服務：`order-api`、`notification-receiver`

### 2. 程式與設計核對
- `src/Program.cs:79-89`：取消成功轉態時才建立通知，notification_id 是隨機產生的 GUID，只在 API 回應和 Log 裡出現。
- 預設路徑是 API 把通知放進佇列（`Program.cs:88`），之後由背景 worker 發送。
- worker 送到接收端且收到成功回應後，才寫 `notify_sent`（`Program.cs:257-261`）。所以 `notify_sent` 只是發送端的紀錄，不能當成接收端已收到。
- 送失敗會重試 3 次，仍失敗就寫 `notify_dead_letter`（`Program.cs:262-266`）。
- `design/design-review.md` 第 7 點寫「本輪未跑 .NET」，這是歷史背景，不代表這次的執行情況。
- 我沒有在這份程式裡看到 `version` 是否等於 `delivery-hardening-local-r2` 的依據。`/version` 的回傳值和 `VERSION` 檔都不在工作區。

### 3. Log 查詢（來源：Grafana MCP `query_loki_logs`）
| 次數 | 條件 | 結果 |
|---|---|---|
| 1 | datasource `day17-unavailable`；`{lab_case="query-failure", service_name="order-api"} \|= "live-20261001-02-query-failure"`；範圍同上；limit 50 | 502，回應內容空白 |
| 2 | 同上，重試一次 | 502，回應內容空白 |

- `service_name` 是我依慣例猜的標籤，沒有先驗證。但 502 是閘道或後端錯誤，應該不是標籤問題。
- 這是工具失敗，不是「查到但沒有資料」。
- 依任務要求，我沒有換資料來源，也沒有擴大查詢範圍。
- 第二次查詢（用 notification_id 查 `notification-receiver`）沒有執行，因為第一次沒有產出 notification_id。我也沒有改用 order_id 去查接收端，因為那不符合 Skill 的流程。

### 4. 缺少的來源
- `order-api` 的 Log，含 `cancel` 與 `notify_sent` 或 `notify_dead_letter` 事件，以及 notification_id。
- `notification-receiver` 用同一個 notification_id 查到的獨立紀錄。
- 已部署版本的確認資料。

### 5. 下一步（需由操作者處理）
1. 修復或確認 `day17-unavailable` 的 Loki 後端能正常回應。我沒有執行 `check_datasources_health`，因為任務指定只查這個來源的 Log。如果你同意，我可以對這一個資料來源做健康檢查。
2. 恢復後，重跑 `order-api` 的 order_id 查詢取得 notification_id，再對 `notification-receiver` 做一次獨立查詢。
3. 我不會補送、不會結案。

```json
{
  "order_id": "live-20261001-02-query-failure",
  "sender_status": "unknown",
  "receiver_status": "unknown",
  "missing_sources": [
    "order-api logs (datasource day17-unavailable, lab_case=query-failure, 2026-09-30T19:26:25Z–19:26:27Z): Loki HTTP 502 x2",
    "notification-receiver logs by notification_id (not runnable: notification_id not obtained)",
    "deployed version confirmation for delivery-hardening-local-r2"
  ],
  "next_action": "操作者修復或確認 day17-unavailable Loki 後端；恢復後以 order_id 查 order-api 取得 notification_id，再獨立查 notification-receiver。不補送、不結案。"
}
```