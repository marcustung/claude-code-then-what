結論已寫入 `out/result.json`，這次只做查詢與分析，沒有補送也沒有結案。

**結論（訂單 r2-healthy-01，版本 delivery-hardening-local-r2，本機教學環境）**
- **通知 ID：** `7e746d20853d48b9b3948c1fe92319c1`
- **發送端：confirmed。**
  - `data/logs.jsonl` 第 2 行：cancel 結果 ok，`transitioned=true`，`refund_requested=true`。
  - 第 3 行：同一個通知 ID 有 `notify_sent`。
  - `src/Program.cs` 的 worker 只在 sink 回成功碼後才記 `notify_sent`。
- **接收端：confirmed。**
  - 依據是 `data/receipts.json` 的獨立收據：status 200，通知 ID、訂單 ID、request_id 都對得上，`attempt=0`，表示第一次就送達。
  - 收據時間比 `notify_sent` 早約 4 毫秒，兩者吻合。
  - 這筆結論來自收據，不是從發送端推得。
- **無關事件：** 日誌裡的 `r2-shipped-01` 因已出貨被拒絕（`rejected_shipped`），不通知，屬正常，不列入本次判定。

**限制與缺件（`missing_sources`）**
- 沒有連遠端 Log server，只有離線資料包。
- 沒有獨立的接收端原始日誌，收據只有一筆 JSON。
- 設計文件說明本輪沒有執行 .NET 測試。
- `design/design-review.md` 第 2 點提到，收據不一定保存 `refund_requested`。這筆收據的 payload 有帶 `refund_requested: true`，與 cancel 日誌一致。

**下一步（`next_action`）**
- 請操作者確認 `receipts.json` 確實是接收端 sink 保存的。
- 若要更強的佐證，可取接收端原始日誌，或執行 payload 測試。

我沒有執行 `collect.py`，這些結論是直接讀原始檔得到的。