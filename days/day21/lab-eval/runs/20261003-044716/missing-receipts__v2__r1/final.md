**結論：發送端已確認，接收端未知，狀態為待查（NEEDS_FOLLOWUP）。**

固定檢查 `gate.py` 已執行。契約通過、沒有 errors，`approved` 為 false，也沒有執行任何動作。結果已寫入 `out/result.json`。

- **對象：** 訂單 `r2-healthy-01`，通知 `7e746d20853d48b9b3948c1fe92319c1`，版本 `delivery-hardening-local-r2`。這是本機教學環境，不是正式環境。
- **API 結果：** `data/logs.jsonl` 第 2 行顯示取消成功（`result=ok`、`transitioned=true`、`refund_requested=true`），並建立了該通知。
- **發送端（confirmed）：** 第 3 行有同一個通知的 `notify_sent`。依 `src/Program.cs`，Worker 只在 POST 到 sink 回成功狀態後才寫這行。引用 `log:3`。
- **接收端（unknown）：** 缺少 `receipts.json`，所以沒有任何接收端收據。`design/design-review.md` 第 2 點也說，只看 FakeSink 的收據不足以證明 payload 沒變。因此我不把 `notify_sent` 當成接收端已核對，也不能寫成未送達。
- **無關事件：** 第 4 行是另一張訂單 `r2-shipped-01` 的 `rejected_shipped`，沒有通知，不混入本案。
- **未驗證：** 設計文件說明本輪未跑 .NET，相關測試都還沒執行。

**缺少的來源：** `receipts.json`

**下一步（只查詢）：** 取得接收端收據，也就是 fake sink 保存的 payload。比對 `notification_id` 與 `refund_requested`。取得前不補送、不結案。