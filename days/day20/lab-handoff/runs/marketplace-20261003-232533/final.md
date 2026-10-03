# 通知查核結果（待查，**固定檢查未執行**）

**範圍**：order `r2-healthy-01`，版本 `delivery-hardening-local-r2`，環境為本機教學 fixture（task.json），非正式環境。無 Log server，只讀本地檔案。

## 卡點
`collect.py` 與 `gate.py` 兩次執行都需要核准而被擋，我沒有強行繞過。因此：
- 拿不到合法的 `records[].ref`，`evidence_refs` 留空，沒有自編。
- 固定檢查未執行，結果**不能算通過**，停在待查。

## 查核依據（直接讀檔，未經 collect.py）

**1. 程式與設計**
- `src/Program.cs:79-88`：只有狀態確實從未取消轉為已取消（`transitioned`）才建立通知。接著寫入 Channel，由 Worker 非同步 POST 到 sink。
- `src/Program.cs:257-261`：`notify_sent` 只在 sink 回成功碼後才計數與寫 log。
- `design/design-review.md` 第 1、2 點：Worker 送達與 HTTP 回應沒有固定先後。只看收據不足以證明 payload 正確，需要接收端觀察。
- 設計第 7 點：本輪未跑 .NET，相關測試都是待執行設計。

**2. 發送端（`data/logs.jsonl`）**
- 第 2 行：`cancel` 結果 `ok`，`transitioned=true`，`refund_requested=true`，`notification_id=7e746d20…c1`。
- 第 3 行：同一個 notification_id 有 `notify_sent`，沒有 `notify_deferred`、`notify_attempt_failed` 或 `dead_letter`。
- 第 4 行：`r2-shipped-01` 因已出貨被拒（`rejected_shipped`），沒有通知，符合 BR-02 / NC-03。這是另一筆訂單，不混入本案。
- 小提醒：第 4 行的 `request_id` 與 `run_id` 沿用 healthy 那筆。這看起來是 fixture 的沿用，我沒有據此下結論。

**3. 接收端（`data/receipts.json[0]`）**
- 收據的 `notification_id`、`order_id`、`request_id` 都與 log 一致，`refund_requested=true`，`attempt=0`，`status=200`。
- 這與 `cancel` log 一致，也與 `Domain` 對「已付款、未出貨、未取消」會提出退款的規則一致。

## 判讀
- 資料面顯示發送端與接收端互相吻合，沒有矛盾。
- `receipts.json` 是 fixture 檔，不是獨立運行的接收端日誌。時間戳（epoch 1790646010.857）也落在 `notify_sent`（10.861）之前約 4ms，與「先收後記」相容，但我不據此推論因果。
- 因為固定檢查未跑，我在結果中把兩個狀態**保守寫成 `unknown`**。依資料實際看來較可能是 `confirmed`，但要等 collect.py 的 ref 到位後再改。

## 已寫入
`out/result.json`：`sender_status=unknown`、`receiver_status=unknown`、`evidence_refs=[]`、`missing_sources` 已列出缺件。

## 缺少與下一步
- 缺：collect.py 的 records、gate.py 結果、.NET 實際執行證據。
- 下一步（需你核准）：執行 `collect.py .`，用其 ref（預期是 log 第 3 行與 `receipt:0`）把兩個狀態更新為 confirmed，再跑 `gate.py .`。若退出碼 1，依 errors 修正後再跑一次。
- 未補送、未結案、未修改 task.json、data/ 與 scripts/。