**結論：目前不能判定是否需要補送，也不建議先補送。**

**已確認**
- 發送端有 `notify_sent`，`sync=true`，ID 為 demo-notify-18（sender-event.json）。這筆是合成資料，並非實際擷取的 Log。
- `sync=true` 只會出現在 `sync_notify` 的同步分支（Program.cs:85-86、222）。這是演練用的故障注入設定，正常是非同步。
- `notify_sent` 只代表發送端收到 HTTP 成功回應（Program.cs:217、257-260），不代表接收端已收到（wiki/notification.md）。
- 通知是在 `TryCancel` 的 lock 之外才建立與送出（Program.cs:79-88）。
- 訂單與 Channel 都在記憶體中（Program.cs:18、102）。

**尚缺**
- 接收端中 notification_id 相同的紀錄（ticket.json：未提供接收端 Log）。
- 部署設定證明。`sync_notify` 是否真的啟用、`OC_SINK_URL` 指向哪裡，都未確認（ticket.json）。
- 補送契約、SLA、授權、具名 Owner（ticket.json、notification.md）。
- `sources/config.alloy` 不在工作目錄，log-query.md 的標籤說明無法核對原始設定。
- 缺 task.json，datasource 也沒有提供（INDEX.md）。

**下一步查哪裡、用什麼條件**
1. 查接收端 Loki：`service_name="notification-receiver"`，時間窗 2026-10-01T00:00:00Z 到 00:05Z，JSON 內容比對 `notification_id=demo-notify-18`，再比對 `order_id=demo-order-18`（log-query.md）。
2. 查發送端 `service_name="order-api"`，看同一 ID 有沒有 `notify_attempt_failed`、`notify_dead_letter`，或重複的 `notify_sent`（Program.cs:219、223）。
3. 判讀：
   - 找到接收紀錄，才算 confirmed，不需補送。
   - 查無結果時，先核對標籤與時間窗，並分清是工具錯誤還是空結果。核對後仍沒有，也只能記為 unknown，不能寫成未送達。

**能否補送**
- 目前不可。Program.cs 沒有補送機制，接收端是否以 notification_id 去重也未知，隨意重送可能造成重複通知。
- 條件：接收端確認未收到，並且 Owner 核准補送方式。

**需要誰決定**
- 需要服務 Owner 決定，但工單沒有指名，我不補寫人選。補送授權與 SLA 也要由業務或 Owner 確認（notification.md「未取得的決策」）。