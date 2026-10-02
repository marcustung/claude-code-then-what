**結論：目前不能判定要補送，也不能判定已送達。** 這張工單缺少接收端證據。

**已確認**
- 發送端事件 `notify_sent`，order_id=demo-order-18、notification_id=demo-notify-18，帶 `sync:true`。來源：sender-event.json。
- 這個事件只代表發送端收到 HTTP 成功。程式在 `resp.IsSuccessStatusCode` 為真時才寫入，SendOnce 在 Program.cs:217、222，worker 在 248、259–260。它不代表接收端處理完成，也不代表使用者收到。來源：wiki/notification.md、applicability.md。
- `sync:true` 對應 `faults.SyncNotify` 分支，通知由請求路徑的 `SendOnce` 同步送出（Program.cs:85–86、222）。但設定是否真的開啟，現有資料無法證明。
- 通知只在 `transitioned` 為真時建立（Program.cs:79–83）。重複取消走 idempotent 分支，不會建通知（Program.cs:76），所以重送取消不能當補送入口。來源：applicability.md 第 3 列。
- 版本一致：ticket 回報與提供的程式都是 delivery-hardening-local-r2。來源：ticket.json。
- 訂單與 Channel 都在記憶體，程序重啟後不能假設資料還在。來源：notification.md。

**尚缺**
- 接收端 log、部署設定證明、補送契約、具名 Owner。來源：ticket.json 的 `available`。
- 本次 `sync_notify` 的實際設定來源。
- 「API 回 200」只是請求紀錄的說法，沒有對應的 cancel 事件可核對。ticket 與 sender-event 都只是合成資料（SYNTHETIC），不是實際擷取的 log。

**下一步查哪裡、用什麼條件**
1. 查接收端 log：`service_name=notification-receiver`，用 notification_id=`demo-notify-18` 串接，時間窗 2026-10-01T00:00:00Z 至 00:05:00Z。來源：log-query.md、ticket.json。
2. 同時查發送端 `service_name=order-api` 的 `cancel` 事件，用 order_id 關聯，確認 transitioned=true 與 notification_id 一致。
3. 零筆結果時，先核對標籤、服務名稱和時間窗，並分清是工具錯誤還是成功但為空。來源：log-query.md。
4. 查當次的部署與設定來源，確認 `sync_notify`。datasource 由 task.json 提供，目前工作目錄沒有這個檔案，所以未知。

**能否補送**
- 目前不可以。證據有三種可能：查到接收紀錄、確認沒有接收紀錄，或查不到任何資料（只能記為 unknown）。補送契約與去重規則也沒有，所以補送授權不成立。來源：applicability.md「缺件與決策」。
- 補送前至少要有：接收端確認未收到、獨立的補送方法，以及接收端去重契約。

**需要誰決定**
- 服務維護者（Owner 未指名，不編造人名）：確認查詢來源與部署版本。
- 有權接受重複通知風險的人：決定補送條件。
- 以上是教學包建議的分工，不是公司已採用的規範。來源：applicability.md。