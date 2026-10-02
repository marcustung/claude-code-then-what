**結論：目前不能判定是否需要補送，也不能授權補送。** 只有發送端證據，沒有接收端證據。

**已確認**
- 發送端事件 `notify_sent` 存在，`sync: true`，order_id 為 demo-order-18，notification_id 為 demo-notify-18（sender-event.json）。該檔是合成資料，不是實際擷取的 log。
- `sync=true` 代表走 sync_notify 的 `SendOnce` 路徑，由請求路徑同步送出。`Program.cs:86、222` 可核對。正常的 worker 路徑不帶 sync（`Program.cs:259-260`）。
- `notify_sent` 只在 `resp.IsSuccessStatusCode` 為真時寫入（`Program.cs:217、222`）。因此它只證明發送端看到 HTTP 成功，不證明使用者收到、接收端處理完成或退款完成（wiki/notification.md；wiki/applicability.md 第 7 列）。
- ticket 的版本與提供的程式版本都是 delivery-hardening-local-r2，一致（ticket.json）。
- 重複取消不是補送入口。已取消時不會再建立通知（wiki/applicability.md 第 9 列，來源 Cancellation.cs 與 Program.cs 的 Transitioned 分支）。

**尚缺**
- 接收端 log，或相同 notification_id 的接收與處理紀錄（ticket.json 的 available 欄）。
- 部署中 sync_notify 設定的證明。程式只說明有這個分支，ticket 的環境標示不是部署證明。
- 補送契約：補送方法、接收端去重規則、授權。
- 具名的 Owner。
- 公司 SLA 與正式接收端也沒有提供（wiki/notification.md「未取得的決策」）。

**下一步查哪裡、用什麼條件**
1. 到接收端 log 查。依 wiki/log-query.md，service_name 用 `notification-receiver`，發送端是 `order-api`。
2. 條件：notification_id = demo-notify-18，order_id = demo-order-18，時間窗 2026-10-01T00:00:00Z/00:05:00Z。這兩個 ID 要從 log JSON 內容比對，不是標籤。
3. 零筆結果先核對標籤、服務與時間窗，並區分工具錯誤與成功的空結果。查不到只能記為 unknown，不等於沒送達（wiki/log-query.md）。
4. 同時向服務維護者確認當次部署的 sync_notify 設定來源。

**能否補送**
- 目前不可以。沒有補送 API、去重契約或授權，補送可能造成重複通知（wiki/applicability.md「缺件與決策」）。
- 只有在查得接收端沒有紀錄，且補送契約與授權都到位後，才能再評估。

**需要誰決定**（wiki 的建議分工，不是公司已採用的規範，也沒有具名人選）
- 服務維護者：確認查詢來源與部署版本。
- 有權接受重複副作用風險的人：決定補送條件。
- 這兩個角色都要由團隊指定，我不編人名。

**限制：** 我只讀了檔案，沒有執行任何指令，也沒有呼叫外部系統。wiki 是教學用資料，不是正式服務手冊。