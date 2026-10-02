**結論：目前不建議補送。** 補送的前提是接收端沒收到，這點還沒確認。

**已確認**
- 這是合成教學工單，只有發送端事件。`demo-notify-18` 的 `notify_sent` 帶 `sync:true`（sender-event.json）。
- 程式版本與回報版本相同，都是 delivery-hardening-local-r2（ticket.json）。
- `sync:true` 代表走 `sync_notify` 同步分支：`SendOnce` 在請求路徑上送出，收到 `IsSuccessStatusCode` 才寫 `notify_sent`（Program.cs:85-86、217、222）。
- 通知只在 `transitioned` 為真時建立（Program.cs:79-83），所以這筆是真的完成了取消。
- 這個事件只證明發送端看到 HTTP 成功。接收端是否 confirmed，另需相同 `notification_id` 的接收紀錄，也沒驗退款（wiki/notification.md:15）。
- 失敗路徑會寫 `notify_dead_letter`（Program.cs:223）。目前沒有證據顯示這筆走到那裡。
- 程式裡沒有補送 API 或補送契約，我只 grep 到發送與重試，沒有補送入口。

**尚缺**
- 接收端紀錄：ticket.json 的 `available` 欄位寫明沒提供。
- 部署設定證明：目前無法確認實際是否開了 `sync_notify`，以及 `OC_SINK_URL` 指向哪裡。只能說事件形狀符合同步分支。
- 補送契約，以及具名 Owner。
- 事件本身是「shaped after」的合成資料，不是真實擷取的 log（sender-event.json）。
- 訂單與 Channel 都在記憶體，程序重啟後的狀態無法推定（notification.md:17）。

**下一步查哪裡、用什麼條件**（依 wiki/log-query.md，需有可用的 log 查詢權限；目前 mcp.json 的 `mcpServers` 是空的，本次沒有可用工具）
1. 接收端：`service_name="notification-receiver"`，時間窗 `2026-10-01T00:00:00Z/00:05:00Z`，用 JSON 內容比對 `notification_id=demo-notify-18`。
2. 發送端：`service_name="order-api"`，同一時間窗，找 `demo-order-18` 的 `cancel` 事件、同一個 `notification_id`，以及是否有 `notify_attempt_failed` 或 `notify_dead_letter`。
3. 先核對標籤與時間窗，再判讀零筆結果。工具錯誤和成功的空結果要分開記。
4. 部署設定要向有權限的人索取，不從 wiki 猜。

**能否補送**
- 接收端若有同 ID 紀錄，就不用補送，問題轉向使用者端或通知內容。
- 接收端若確定沒有，才有補送理由。但目前沒有補送契約，也沒有授權與冪等保證。重送時 `notification_id` 是否沿用、接收端是否去重，都沒有來源可證。所以現在不能直接補送。
- 只查到「沒有紀錄」時只能記為 unknown，不能判定未送達（log-query.md:12）。

**需要誰決定**
- 服務 Owner：確認補送行為、接受條件與授權。ticket 沒有指定具名人選，需要工單方指派（notification.md:19-21）。
- 接收端維護者：確認去重與重送是否安全。來源沒有提到這個角色，是我的建議。