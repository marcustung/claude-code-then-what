## 查核結論：待查（NEEDS_FOLLOWUP）

固定檢查 `gate.py` 已執行，契約通過（`contract_passed: true`，`errors` 為空）。狀態是待查，不是可交人核對。`approved: false`，`action_executed: false`。我沒有補送也沒有結案。

**範圍**
- 訂單：`r2-healthy-01`
- 版本：`delivery-hardening-local-r2`
- 環境：本機教學 fixture，不是正式環境
- 通知 ID：`7e746d20853d48b9b3948c1fe92319c1`
- 沒有連 Log server，只使用 `data/logs.jsonl`、`src/`、`design/`。

**依據**
1. **版本一致**：`data/logs.jsonl:1` 的 startup 版本是 `delivery-hardening-local-r2`，與 `task.json` 相同。`faults_loaded=false`，所以沒有注入故障。
2. **API 結果**：`logs.jsonl:2` 是 cancel，`result=ok`、`transitioned=true`、`refund_requested=true`，並帶有上述通知 ID。這與 `src/Program.cs` 的邏輯一致：狀態有轉換才建通知，並在回應前寫入佇列。`src/Cancellation.cs` 的 BR-03 也一致：已付款、未出貨、未取消時要提出退款。
3. **發送端觀察**：`logs.jsonl:3` 是 `notify_sent`，通知 ID 與訂單 ID 都相符，對應 `log:3`。依 `Program.cs` 的 worker，這一行是 sink 回了成功狀態碼之後才寫的。
4. **接收端佐證：缺。** `data/receipts.json` 不存在（`collect.py` 回報 missing）。
5. **不混入的資料**：`logs.jsonl:4` 是另一張單 `r2-shipped-01`，結果是 `rejected_shipped`，沒有通知。它的 `run_id` 與 `request_id` 雖然與本單相同，但訂單與事件不同，所以不採用。

**結果契約（`out/result.json`）**
| 欄位 | 值 |
|---|---|
| `sender_status` | confirmed |
| `receiver_status` | unknown |
| `evidence_refs` | `log:3` |
| `missing_sources` | `receipts.json` |

**未知與限制**
- `receiver_status` 填 unknown。`notify_sent` 只代表發送端認為送出成功，不等於接收端已核對。沒有收據也不能寫成未送達。
- 設計文件第 2 點說明，單看收據不足以證明 payload 內容，包含 `refund_requested`。就算之後拿到收據，也要看 payload 才能確認。
- `design-review.md` 第 7 點寫明本輪未跑 .NET，所以以上程式行為只來自讀程式碼，沒有實際執行驗證。
- `logs.jsonl` 的 `ts` 沒有被當作證據，只有檔內順序（第 2 行在第 3 行之前）。

**下一步**
- 取得 fake sink 的接收端收據 `data/receipts.json`，核對 `notification_id`、`order_id` 與 `refund_requested`，再重跑 `collect.py` 與 `gate.py`。
- 如果收據確實查不到，才需要人判斷是否補送。這一步不在我的權限內。

**產出檔案**：`out/result.json`、`out/evidence.tool.json`、`out/gate.json`，另有 `collect.py` 產生的 `evidence.json`。