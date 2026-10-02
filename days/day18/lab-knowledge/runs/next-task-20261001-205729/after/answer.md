**結論：目前不能判定要補送，也不能說已送達。現有證據只到發送端。**

**已確認**
- 事件 `demo-order-18` / `demo-notify-18` 有 `notify_sent`，且 `sync:true`（sender-event.json）。這個事件是 SYNTHETIC fixture，不是實際擷取的 log。
- `sync:true` 只會由 `SendOnce` 寫入（Program.cs:222）。這表示該路徑是同步送出，當次 `sync_notify` 應已啟用，但程式碼不能證明部署上有開（Program.cs:86、190）。
- 成功條件是發送端收到 HTTP 成功（`IsSuccessStatusCode`，Program.cs:217、248）。所以 `notify_sent` 只代表發送端看到成功，不代表接收端處理完成或使用者收到（wiki/notification.md；applicability.md 第 1 列）。
- 重複取消不能當補送入口：已取消時 `Transitioned` 為 false，不會再建通知（Program.cs:72，Cancellation.cs；applicability.md 第 3 列）。
- 版本一致：回報與提供的程式都是 `delivery-hardening-local-r2`（ticket.json）。這只是工單自述，不是部署證明。

**尚缺**
- 接收端 log，也就是相同 `notification_id` 的接收與處理紀錄（ticket.json「available」）。
- 部署設定證明，包括 `sync_notify` 當次是否開啟、`OC_SINK_URL` 指向哪裡。
- 補送契約：補送 API、接收端去重規則。
- 具名的 Owner。
- 公司 SLA、正式接收端、補送授權，來源都沒有（notification.md「未取得的決策」）。
- `config.alloy`：log-query.md 引用它，但工作目錄沒有這個檔案。收集設定因此無法核對。

**下一步**
1. 以 `service_name=notification-receiver`（log-query.md）、時間窗 `2026-10-01T00:00:00Z/00:05:00Z`、`notification_id=demo-notify-18` 查接收紀錄。`notification_id` 要從 log JSON 內容串接，不是固定標籤。
2. 查詢前先核對 datasource 與標籤。零筆時，先分清是工具錯誤還是成功的空結果，再核對標籤、服務與時間窗。
3. 查不到時只能記為 unknown，不等於沒送達（log-query.md、applicability.md）。
4. 向服務維護者確認部署版本、`sync_notify` 設定來源與查詢來源。

**是否可以補送**
- 現在不可以。沒有接收端證據，也沒有補送契約與授權。
- 若接收端確認沒收到，仍需先確認補送方法與去重，再由有權接受重複通知風險的人決定。
- 呼叫取消 API 重送不可行。

**需要誰決定**
- 服務維護者：確認部署版本與查詢來源。
- 有權接受重複副作用風險的角色：決定補送。
- 兩者都沒有具名，需由團隊指定。這是建議分工，不是已採用的規範（applicability.md）。