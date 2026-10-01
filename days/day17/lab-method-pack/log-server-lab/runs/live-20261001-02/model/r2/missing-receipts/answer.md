## 查核結果(order_id `live-20261001-02-missing-receipts`)

**結論:** 發送端有 `notify_sent` 紀錄。接收端在指定窗內沒有任何資料,所以接收端只能標 unknown,不能寫成「未送達」。

### 程式與設計(部署版本 `delivery-hardening-local-r2`)
- `src/Program.cs:79-88`:取消狀態轉換成功時建立通知。正常路徑是 `channel.Writer.WriteAsync`,由 Worker 非同步送出。
- `src/Program.cs:257-261`:`notify_sent` 只在 sink 回應 `IsSuccessStatusCode` 後才寫。
- 這代表 HTTP 成功是發送端觀察。接收端是否留下紀錄,仍需接收端 Log 佐證。
- `design/design-review.md` 第 2 點也說,FakeSink 單看收據不足以下結論。其中「本輪未跑 .NET」是當時的說明,我沒有當成本次執行情況。

### Log 查詢(datasource `day17-loki`,窗口 2026-09-30T19:26:23Z ~ 19:26:25Z)
1. `{lab_case="missing-receipts", service="order-api"} |= "<order_id>"`:0 筆。原因是標籤名稱用錯。
2. `list_loki_label_names`:實際標籤是 `filename`、`lab_case`、`service_name`,沒有 `service`。
3. `{lab_case="missing-receipts", service_name="order-api"} |= "<order_id>"`:2 筆,來源 `/logs/missing-receipts/api/logs.jsonl`。
   - `cancel` 事件:`result=ok`、`transitioned=true`、`refund_requested=true`、`queue_depth=0`,`notification_id=bda1a73ba5f84cb1abcc6d0f265e1e95`。
   - `notify_sent` 事件:`notification_id` 相同,時間約在 `cancel` 事件後 37 ms。
   - 兩筆的 `version` 都是 `delivery-hardening-local-r2`,與 task.json 一致。
4. 獨立接收端查詢:`{lab_case="missing-receipts", service_name="notification-receiver"} |= "bda1a73ba5f84cb1abcc6d0f265e1e95"`:0 筆(查詢成功,無符合資料)。
5. `query_loki_stats`,同一接收端選擇器:streams=0、chunks=0、entries=0。窗內根本沒有 `notification-receiver` 的串流。統計只能輔助判斷,不能代替實際 Log。

### 判讀與未知
- **API 結果:** 取消成功並建立通知,已確認。
- **發送端:** 找到相符的 `notify_sent`,可見 Worker 收到 sink 成功回應。
- **接收端:** 查詢成功但無資料。可能是接收端 Log 沒被收進 Loki,也可能是標籤不同,或接收端確實沒收到。這三種可能我目前無法區分。
- 我沒有擴大時間窗,也沒有換資料來源,因為範圍限定在 task.json 指定的窗口與 lab_case。

### 下一步(最小補查,需操作者決定)
1. 請確認 `notification-receiver` 的 Log 是否有被收進 Loki,以及它使用的標籤名稱。
2. 若要查時間偏移,需要操作者授權後,才能用同一個 `notification_id` 在同一 lab_case 加寬時間窗重查。
3. 我不會補送、恢復資料或結案。

```json
{
  "order_id": "live-20261001-02-missing-receipts",
  "sender_status": "confirmed",
  "receiver_status": "unknown",
  "missing_sources": [
    "notification-receiver logs for lab_case=missing-receipts in 2026-09-30T19:26:23Z~19:26:25Z (query returned 0 lines; stats streams=0)"
  ],
  "next_action": "請操作者確認 notification-receiver 的 Log 是否已收進 day17-loki 及其標籤;取得後用 notification_id bda1a73ba5f84cb1abcc6d0f265e1e95 重做接收端查詢。在有接收端證據前不判定未送達,也不補送或結案。"
}
```