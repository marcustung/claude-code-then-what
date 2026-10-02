**結論:** 任務要求 r3,但只提供 r2 原始碼。以下都只適用 r2。r3 的差異沒有來源,列為未知。

| 原說法 | 來源 | 判定與理由、範圍 |
|---|---|---|
| TryCancel 在同一 lock 內取得、判斷、寫回 | Program.cs:105-113 | **保留**。只限同程序、同一 store 的這三步。 |
| design-review 第4點:個別 lock 不保證並行取消安全 | design-review.md:6 | **修訂**。r2 已不適用,限定範圍見 changes.md。其行號(API:69、84、88)與 r2 不符,不採用。 |
| 通知建立與入列在 lock 外,非持久化交易 | Program.cs:79-88 | **保留**。 |
| 正常為非同步,sync_notify 走 SendOnce | Program.cs:85-88 | **保留**。 |
| notify_sent 由 worker 在 HTTP 成功後寫入 | Program.cs:257-260、222 | **修訂**。sync_notify 時是 SendOnce 寫入,帶 `sync=true`。 |
| 訂單與 Channel 在記憶體 | Program.cs:15、18 | **保留**。logs.jsonl 是檔案(:160),不可說重啟就消失。 |
| (原文未提)重試與 dead letter | Program.cs:195、242-266 | **補充**。失敗重試 3 次(200/400/800ms),仍失敗只記 log 與計數,程式內沒有可補送的儲存。 |
| (原文未提)notify_drop_over_queue 與 notify_delay_ms | Program.cs:230-240 | **補充**。這是演練注入,不是自然行為。 |
| 「本輪未跑 .NET」 | design-review.md:9 | **保留為時間限定**。我這次也沒執行程式。 |
| SLA、正式接收端、補送授權、值班 Owner | notification.md:21 | **未知**。不補造。 |
| 退款完成 | Program.cs | **未知**。`refund_requested` 只是旗標。 |
| r3 的任何變更與設計理由 | 無 | **未知**。 |

**notification.md 修訂草稿**
1. 標題適用版本改為:「已核對 r2;r3 未提供來源,待確認」。
2. 在「正常非同步路徑」段後加一句:「sync_notify 時 notify_sent 由 SendOnce 寫入(sync=true)」。
3. 新增一段:「失敗重試 3 次(200/400/800ms),仍失敗只記 notify_dead_letter 的 log 與計數,沒有補送機制。notify_drop_over_queue 與 notify_delay_ms 是演練注入。」
4. 在「未取得的決策」加一行:「r3 差異、為何通知放在 lock 外,均無來源」。

**待確認:** 請提供 r3 的 Program.cs 與 Cancellation.cs,再核對是否沿用上述結論。