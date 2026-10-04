已寫入 `out/result.json`。結論是：發送端 confirmed，接收端 unknown。

**查核依據（離線，直接讀原件，未執行 collect.py）**
- **版本**：`logs.jsonl` 的版本是 `delivery-hardening-local-r2`，和 `task.json` 一致。
- **發送端**：`logs.jsonl:2` 顯示訂單 `r2-healthy-01` 取消成功，`transitioned=true`，通知ID 是 `7e746d20…`。`logs.jsonl:3` 有同一ID的 `notify_sent`。
- **收據**：`receipts.json` 有同一訂單的收據，但通知ID是 `3f1c9a7e…`，和發送紀錄的 `7e746d20…` 不同。
- **程式**：`src/Program.cs` 裡，`notify_sent` 只代表 sink 回應成功。通知ID 由 `Guid.NewGuid` 在每次轉換時產生。所以只憑訂單ID相同，不能把這張收據當成這則通知的接收證據。
- **設計**：`design-review.md` 第 2 點說明，單看收據不足以證明接收端已核對。

**不確定的部分**
- 沒有任何接收端紀錄能對上 `7e746d20…`。
- 收據 `3f1c9a7e…` 在發送端 Log 裡找不到對應紀錄，來源不明。可能是另一次請求或測試資料，這點無法由現有資料判斷。
- 因此不能說「沒送達」，只能標 unknown。

**缺少的來源**
1. 接收端對 `7e746d20…` 的收據或 Log。
2. `3f1c9a7e…` 的發送端紀錄。
3. 真實 Log server（本次沒有連線）。

**下一步**
- 向接收端查 `7e746d20…` 有沒有收據。
- 追查 `3f1c9a7e…` 的來源。
- 在取得對應收據前，接收端維持 unknown。
- 本次只查詢與分析，沒有補送也沒有結案。