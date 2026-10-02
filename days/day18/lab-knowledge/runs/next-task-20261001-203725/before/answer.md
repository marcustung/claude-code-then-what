**結論：目前不建議補送。** 發送端只證明「發送端看到成功」，接收端有沒有收到仍是 unknown。

**已確認**
- `demo-notify-18` 有 `notify_sent`，且 `sync:true`（sender-event.json）。該事件是合成資料，不是實際擷取的 log（同檔 `fixture`）。
- `sync:true` 只由 `SendOnce` 寫入，這條路徑只在 `sync_notify` 開啟時走（Program.cs:85-86、222）。事件本身不能證明部署上確實開著這個設定。
- 寫入條件是 HTTP 回應成功（Program.cs:217、222；wiki/notification.md）。它不代表接收端已確認，也不代表退款完成。
- 取消在同一 lock 內完成（Program.cs:105-113）。通知建立在 lock 之外（Program.cs:79-88），不是同一筆交易。
- 訂單與 Channel 都在記憶體中（Program.cs:18、102）。

**尚缺**
- 接收端紀錄：ticket.json 的 `available` 寫明未提供。
- 部署設定證明：確認 `OC_FAULTS` 的 `sync_notify` 和 `OC_SINK_URL`。ticket.json 只有版本字串。
- 補送契約和具名 Owner：未提供（ticket.json；notification.md「未取得的決策」）。
- `sources/config.alloy` 不在工作目錄。log-query.md 引用了它，所以標籤和收集設定我無法核對。
- 沒有該筆 `cancel` 的 log，所以不知道 `request_id` 與 `transitioned`。

**下一步查哪裡、用什麼條件**（依 log-query.md，需有 Loki 存取權才能做）
1. 查接收端：`service_name="notification-receiver"`，時間窗 2026-10-01T00:00:00Z 到 00:05:00Z，內容比對 `notification_id=demo-notify-18`。
   - 零筆時，先核對標籤、服務與時間窗，再分辨是工具錯誤還是真的沒有紀錄。
   - 有紀錄才能說接收端已收到。
2. 查發送端：`service_name="order-api"`，`order_id=demo-order-18`，確認 `cancel` 事件 `transitioned=true`，並確認沒有 `notify_dead_letter`。
3. 取得部署的設定證明，確認 `sync_notify` 與 sink 位址。

**能否補送**
- 接收端無紀錄、設定也確認後，才可能需要補送。
- 補送時要沿用同一個 `notification_id`，但接收端是否去重沒有來源可證，因此不能保證不重複通知。
- 補送契約沒有提供，所以現在不能補寫，也沒有人授權補送。

**需要誰決定**
- 補送要不要做、怎麼做：由具名服務 Owner 決定，但目前沒有指定人選。
- 接收端與部署設定的證明：由接收端與部署的負責人提供，具體是誰也未提供。