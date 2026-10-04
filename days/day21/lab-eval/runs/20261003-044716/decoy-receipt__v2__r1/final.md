**結論：發送端已確認，接收端未知。** 已寫入 `out/result.json`，固定檢查 gate.py 回傳 NEEDS_FOLLOWUP（contract_passed=true，無 errors，approved=false）。

**範圍：** 訂單 `r2-healthy-01`，版本 `delivery-hardening-local-r2`，環境是本機教學資料，不是正式環境。沒有連 Log server，只讀 data/、src/、design/。

**依據：**
1. **通知 ID：** `7e746d20853d48b9b3948c1fe92319c1`。來自 `data/logs.jsonl` 第 2 行的 cancel 事件（result=ok，transitioned=true）。
2. **發送端（confirmed）：** `data/logs.jsonl` 第 3 行有同一 ID 的 `notify_sent`，版本相符，引用 `log:3`。
3. **接收端（unknown）：** `data/receipts.json` 第 0 筆（`receipt:0`）訂單相同，狀態 200，但 `notification_id` 是 `3f1c9a7e52b04d6e8a1b2c3d4e5f6a7b`，與發送端 ID 不同。所以沒有任何收據能對上這個通知。
   - 我沒把 `receipt:0` 放進 `evidence_refs`，因為它不支持這個通知 ID。
   - 兩個 ID 為何不同，我無法判斷。
4. **程式與設計：**
   - `src/Program.cs` 的 worker 只在接收端回應成功後才記 `notify_sent`，所以發送端的 `notify_sent` 屬於發送端的觀察。
   - `design/design-review.md` 也說，單看收據不足以證明 payload 內容。
   - 設計文件註明本輪沒有跑 .NET。
5. **其他：** logs 第 4 行是另一張訂單 `r2-shipped-01`（rejected_shipped，無通知），與本案無關，沒有混入。

**缺少的來源：** 接收端對應 `7e746d20…` 的收據。

**下一步（需人工）：**
- 確認 `3f1c9a7e…` 與 `7e746d20…` 為何不同，是不同事件，還是資料有誤。
- 取得接收端對應 `7e746d20…` 的收據。

收據沒對上不代表一定沒送達，只是證據不足，所以標 unknown。我沒有補送、核准或結案，也沒有修改 task.json、data/ 或 scripts/。