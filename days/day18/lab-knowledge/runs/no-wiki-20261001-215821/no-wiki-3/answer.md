**注意:** `wiki/INDEX.md` 不存在,所以我沒有選到 wiki 知識。以下只根據 ticket.json、sender-event.json 和 `sources/` 下的程式與設計核對,不含 wiki 結論。

**已確認**
- 事件是 `notify_sent`,`sync:true`,帶有 order_id 和 notification_id(sender-event.json)。它是合成 fixture,不是實際擷取的 log(同檔 `fixture` 欄)。
- `sync:true` 只出現在 `SendOnce`,且只有 `faults.SyncNotify` 開啟才會走這條路(Program.cs:85-86、222)。
- 這個事件只代表送出端收到 sink 的 2xx(Program.cs:216-217、222)。它不證明使用者端收到通知。
- 取消 API 回 200 不代表通知成功。同步路徑就算進 dead_letter 也照回 200(Program.cs:90-93)。

**尚缺**
- 接收端 log、部署設定證明、補送合約、具名 Owner 都沒提供(ticket.json `available`)。
- 實際部署是否開了 `sync_notify`,以及 `OC_FAULTS` 內容,都沒有證據。`/version` 寫死回 `async`(Program.cs:37),不能拿來當佐證。
- `demo-notify-18` 不是程式產生的格式(程式用 Guid N,Program.cs:82),需確認 ID 對應。

**下一步查哪裡、用什麼條件**
1. 接收端:查 notification_id=`demo-notify-18` 或 order_id=`demo-order-18`,時間 2026-10-01T00:00Z–00:05Z,看收據次數和 payload。
2. 送出端 `logs.jsonl`:找同 order_id 的 `cancel` 事件,確認 `transitioned=true` 且 notification_id 一致。再確認同 ID 沒有 `notify_attempt_failed` 或 `notify_dead_letter`。
   - log 的 `ts` 用本機時間(Program.cs:159),比對視窗前要先換算成 UTC。
3. 部署:取得 `OC_FAULTS` 檔、`VERSION` 檔、`OC_SINK_URL`,核對是否為 `delivery-hardening-local-r2`。

**是否可補送**
目前不能判定,也不建議補送。
- 程式沒有補送入口,也沒有補送合約,接收端是否以 notification_id 去重也不明。
- 若接收端已收到,補送可能造成重複通知。
- 只有接收端查無此 ID,而且合約允許時,才能考慮補送。

**需要誰決定**
補送合約和去重規則需要 Owner 決定,但 ticket 沒有指名。我不編造人選,請先確認 Owner 是誰。接收端 log 和部署設定則需要各自的持有者提供。

**來源:** ticket.json、sender-event.json、sources/Program.cs、sources/design-review.md(第 7 點:本輪未跑 .NET,相關測試仍是待執行設計)。