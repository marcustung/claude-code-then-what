# 事件

- 症狀：呼叫端送通知時逾時（timeout），沒有拿到回應。
- 通知內容：{"notificationId": "notice-01", "orderId": "order-01", "requestId": "request-01", "kind": "order_cancelled", "refundRequested": true}
- 操作者授權範圍（唯讀資訊，由操作者設定）：Owner 已核准 notice-01 的補做，最多 1 次，目前沒有凍結。
- 補做只能由固定入口執行，入口會自己再查一次接收端並核對授權。
