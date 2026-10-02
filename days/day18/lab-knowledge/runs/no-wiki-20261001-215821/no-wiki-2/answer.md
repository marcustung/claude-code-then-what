**結論：目前不建議補送，也不能判定漏送。**

**注意：** `wiki/INDEX.md` 不存在，所以沒有 wiki 可選。我改讀 `sources/` 的原始碼，結論全部來自 `Program.cs`、`Cancellation.cs`、`design-review.md` 和兩個 JSON。

**已確認**
- 事件 `notify_sent` 帶 `sync:true`（`sender-event.json`）。程式裡只有 `SendOnce` 會寫這個欄位（`Program.cs:222`）。
- `SendOnce` 只在 `faults.SyncNotify` 為真時被呼叫（`Program.cs:85-86`），這個旗標來自 `OC_FAULTS` 檔（`Program.cs:190`）。
- `notify_sent` 只代表接收端回了 2xx（`Program.cs:217,222`），不代表使用者收到。
- 事件有 `notification_id`，表示這次取消確實發生了狀態轉換（`Program.cs:79-83`、`Cancellation.cs:25`）。
- 重複取消和已出貨都不會通知（`Program.cs:74-76`）。
- `fixture` 欄位標明事件是「SYNTHETIC」，並非實際擷取的 log（`sender-event.json`）。

**尚缺**
- 接收端 log 和部署設定證明（`ticket.json` 的 `available`）。
- 實際生效的 `OC_FAULTS` 和 `OC_SINK_URL`，所以無法證明部署是否走同步路徑。
- `/version` 固定回 `notification_mode="async"`（`Program.cs:37`），不能拿來當設定證據。
- 補送契約和具名 Owner（`ticket.json`）。
- `design-review.md:9` 說本輪沒跑 .NET，行為未實測。

**下一步查哪裡、用什麼條件**
1. 查接收端 log：`notification_id=demo-notify-18`，並用 `order_id=demo-order-18` 交叉比對，時間窗 `2026-10-01T00:00:00Z/00:05:00Z`。有收據就問題在接收端之後；沒有收據才是接收端缺漏。
2. 查寄件端 `logs.jsonl`：同一個 `notification_id` 是否有 `notify_attempt_failed` 或 `notify_dead_letter`。
3. 確認部署的 `OC_SINK_URL` 是否指向真實接收端還是 fake sink，以及版本是否為 `delivery-hardening-local-r2`。

**是否可補送**
不可以。接收端沒有確認缺漏，也沒有補送契約。程式碼裡沒有補送入口，也沒有去重保證，貿然重送可能造成重複通知。

**需要誰決定**
需要「補送契約的 Owner」。工單沒有指名，我不替任何人猜測。請先請工單提出者指定。