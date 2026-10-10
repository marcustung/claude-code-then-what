# 通知逾時後的處置規則

- 呼叫端逾時只代表呼叫端沒拿到回應，不代表接收端沒做。
- 處置前先查接收端 `/receipt`。回應欄位：source、notification_id、order_id、request_id、generation（接收端看到的嘗試數）、attempt_closed（前次嘗試是否已結束）、status（completed／in_progress／not_completed／unknown）、receipt。
- 查詢失敗、來源不是接收端、ID 對不上，都不是「未完成」的證據。
- 只有在 `attempt_closed=true` 且 `status=not_completed` 時，才可以建議補做；補做仍要經操作者授權與重試上限核對，由固定入口執行。
- 已完成就不重送；重送同一通知，接收端會去重，但仍會多一次 HTTP 嘗試。
