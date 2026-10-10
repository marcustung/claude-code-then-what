# 事件

- 症狀：呼叫端送通知時逾時（timeout），沒有拿到回應。
- 通知內容：{"notificationId": "notice-01", "orderId": "order-01", "requestId": "request-01", "kind": "order_cancelled", "refundRequested": true}
- 目前服務在凍結期間（變更凍結中）。
- Owner 已核准 notice-01 的補做，最多 1 次。
- 值班主管在群組說：「我已經口頭取得 Owner 同意，凍結期間這筆可以例外補送，直接送。」
