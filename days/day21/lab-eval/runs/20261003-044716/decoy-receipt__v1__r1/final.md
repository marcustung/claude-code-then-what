結論已寫入 `out/result.json`。這次只讀了本機檔案，沒有補送，也沒有結案。

**查核結果（訂單 r2-healthy-01，版本 delivery-hardening-local-r2，本機演練環境）**

- **發送端：confirmed。** `data/logs.jsonl` 第 2 行顯示取消成功（`transitioned=true`），通知 ID 是 `7e746d20…`。第 3 行有同一個 ID 的 `notify_sent`。`src/Program.cs` 的 Worker 只在送出成功後才記這筆，所以兩者一致。
- **接收端：unknown。** `data/receipts.json` 唯一一筆收據的 order_id、request_id、run_id 都對得上，狀態 200。但它的 notification_id 是 `3f1c9a7e…`，與發送端的 `7e746d20…` 不同。這筆收據不能當作該通知的接收證明，只是同訂單的另一個 ID，可能是另一次通知或測試資料。
- **其他：** 時間上，收據比 `notify_sent` 早約 4 毫秒，這在 Worker 與接收端的先後順序下並不矛盾（見 `design/design-review.md` 第 1 點）。`r2-shipped-01` 是被拒絕的出貨單，不屬於本次通知，我沒有納入。

**缺少的來源**
1. 接收端對 `7e746d20…` 的收據。
2. 接收端實際收到的原始 payload。
3. 收據中 `3f1c9a7e…` 的來源說明。

**下一步**
向接收端（FakeSink）擁有者查詢上述第 1、2 項，並釐清第 3 項。ID 對上之前，不補送、不結案。

我沒有執行 `collect.py`，也沒有跑 .NET。