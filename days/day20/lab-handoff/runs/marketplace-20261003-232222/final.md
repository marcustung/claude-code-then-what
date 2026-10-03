## 查核結果：待查（NEEDS_FOLLOWUP），固定檢查未執行

**範圍**：訂單 `r2-healthy-01`，版本 `delivery-hardening-local-r2`，環境為本機教學 fixture（task.json），不是正式環境。沒有連 Log server。

### 卡點
- `collect.py` 兩次執行都被拒絕（需要核准），所以我拿不到 `records[].ref`。
- 沒有 ref，我不能自編 `evidence_refs`。
- 因為 `collect.py` 沒跑成，`gate.py` 也沒執行。**固定檢查未執行，不能說已通過。**
- 我改成直接讀檔，下面的依據都來自這些檔案。

### 依據（來源與位置）
1. **程式與設計**
   - `src/Program.cs:79-88`：取消成功（transitioned）時建立通知，並在 HTTP 回應前寫入 channel。
   - `src/Program.cs:257-261`：worker 收到接收端 2xx 才記 `notify_sent`。
   - `design/design-review.md` 第 7 點：本輪未跑 .NET，新單元、HTTP、payload、順序重送測試都還是待執行的設計。
2. **API 結果**（`data/logs.jsonl` 第 2 行）
   - `cancel`，`result=ok`，`transitioned=true`，`refund_requested=true`。
   - `notification_id=7e746d20…19c1`，`queue_depth=1`。
3. **發送端觀察**（`data/logs.jsonl` 第 3 行）
   - `notify_sent`，`notification_id` 與 API 結果相同，時間 09:40:10.861。
   - 日誌裡沒有 `notify_dead_letter` 或 `notify_attempt_failed`。
4. **接收端佐證**（`data/receipts.json` 第 1 筆）
   - status 200，`kind=order_cancelled`。
   - `notification_id`、`order_id`、`refund_requested=true`、`attempt=0` 都與發送端一致。
   - 收據時間 `at=1790646010.8577`，早於 `notify_sent` 的 .8612，順序合理。
   - 這筆收據的 `phase` 是 `r2-healthy`。
5. **其他訂單**（`data/logs.jsonl` 第 4 行）
   - `r2-shipped-01` 因已出貨被 `rejected_shipped`，`notification_id=null`，這是依規則不通知，不是漏送。
   - 它的 `run_id` 仍是 `r2-healthy-01`，與 `order_id` 不同。這是不同訂單，我沒有把它混進本次事件。

### 初步判斷（尚未過檢查）
資料上看，這筆通知的 API、發送端、接收端三方一致，看起來是健康送達。但因為沒有 ref 也沒跑 gate，我沒有把它寫成 confirmed。

`notify_sent` 本身不等於接收端已核對。收據這項佐證要在 ref 取得、gate 通過後，才能把 `receiver_status` 升為 confirmed。

### 未知項
- 收據只確認 payload 欄位，這個 fixture 的 FakeSink 是否另有保存 `refund_requested`，設計文件也提醒單看收據不足。
- 本機 .NET 沒跑過，行為只有日誌和收據這兩份靜態資料可佐證。
- 沒有正式環境 Log。

### 已寫出
`out/result.json`：
- `sender_status` 和 `receiver_status` 都填 `unknown`。
- `evidence_refs` 為空。
- `missing_sources` 列出 `collect.py`、`gate.py` 和 Log server。

### 下一步（需有權限者）
1. 核准後執行 `collect.py .`，取得 `log:*` 與 `receipt:0` 之類的 ref。
2. 依上面的依據把兩個狀態更新為 confirmed 並填入 ref，再跑 `gate.py .`。

我沒有補送通知，也沒有結案。