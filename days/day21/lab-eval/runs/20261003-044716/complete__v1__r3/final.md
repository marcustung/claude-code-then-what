我已把結論寫入 `out/result.json`。訂單 `r2-healthy-01` 的取消通知，發送端和接收端都有對應資料，兩邊都判為 confirmed。

**查核依據**（全是離線本機演練資料；沒有 Log server，也沒跑 `collect.py`）
- **取消事件：** `data/logs.jsonl` 第 2 行顯示取消成功（`result=ok`、`transitioned=true`、`refund_requested=true`），通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`。
- **發送端：** 第 3 行 `notify_sent` 的通知 ID 相同，時間是 09:40:10.861（+08:00）。
- **程式對照：** `src/Program.cs` 只在狀態真的轉換時才建通知，而且是 worker 送到接收端（sink）成功後才記 `notify_sent`。所以發送端 confirmed。
- **接收端：** `data/receipts.json` 有一筆接收端收據，HTTP 200，通知 ID、訂單 ID、request ID 都相符。內容是 `order_cancelled`、`refund_requested=true`、`attempt=0`，時間約 09:40:10.858，早於 `notify_sent` 的 .861，順序合理。這筆收據是獨立的接收端來源，不是由發送端推得，所以接收端 confirmed。
- **無關紀錄：** logs 第 4 行是另一張訂單 `r2-shipped-01`。它因已出貨被拒（`rejected_shipped`），沒有通知 ID，也不該通知，與本案無關。

**限制與未知**
- 這是本機演練環境，不是正式環境，結論只適用這份資料。
- 沒有 metrics 快照，看不到 `notify_sent_total` 和 dead-letter 計數。
- 收據沒有版本欄位，版本 `delivery-hardening-local-r2` 只靠發送端 log 佐證。
- `design/design-review.md` 寫明本輪未跑 .NET，設計內容只作對照，不當作實測。

**建議下一步：** 不需要補送。若要用在正式環境，請由操作者用同一個通知 ID 向真實 Log server 和接收端對帳。我只做了查詢與分析，沒有補送也沒有結案。