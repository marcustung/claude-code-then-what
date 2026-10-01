# 通知查核：r2-healthy-01（本機教學封存，非正式環境）

## 1. 資料身分與缺件
- `task.json:2-4` 的 order_id 與版本是 `delivery-hardening-local-r2`。`data/logs.jsonl:1-4` 每行的 version 都相符。
- 這只證明 log 寫入的版本字串相符，不能證明部署的執行檔就是這一版。`VERSION` 檔不在本目錄。
- `evidence.json:4-7` 記錄 `logs.jsonl` 存在，`receipts.json` 缺失。
- `evidence.json:46` 的 `receipts: []` 是因為來源缺失，不是接收端回報零筆。缺資料不等於零次事件。
- `evidence.json` 已存在，我沒有執行 `collect.py`。

## 2. API 結果
- `logs.jsonl:2`：order_id 是 r2-healthy-01，result 是 `ok`，transitioned 是 true，refund_requested 是 true，notification_id 是 `7e746d20…19c1`。
- 這與程式一致。`Cancellation.cs:19-21` 只在未出貨的訂單上取消並判斷退款，`Cancellation.cs:25` 定義 Transitioned。`Program.cs:79-88` 在 transitioned 時建立通知並入列。
- `logs.jsonl:4` 是另一張單 `r2-shipped-01`：`rejected_shipped`，notification_id 為 null，沒有通知。這符合 `Program.cs:74` 的規則，與本單無關。
- 它沿用同一個 request_id `r2-healthy-request`，比對時要以 order_id 與 notification_id 為準，不能只靠 request_id。

## 3. 發送端觀察
- `logs.jsonl:1`：`faults_loaded:false`，所以 `sync_notify` 與 `notify_drop_over_queue` 等演練故障未啟用，走非同步路徑（`Program.cs:88`）。
- `logs.jsonl:3`：`notify_sent` 的 notification_id 與 order_id 都對得上。這行沒有 `sync` 欄位，符合 worker 路徑 `Program.cs:260`，不是同步路徑 `Program.cs:222`。
- 兩個事件相隔約 40 ms（`…10.8208978` 到 `…10.8612684`）。整段 log 沒有 `notify_attempt_failed`、`notify_deferred` 或 `notify_dead_letter`。
- `Program.cs:257-261` 只在 `resp.IsSuccessStatusCode` 後才寫 `notify_sent`，所以發送端觀察到 sink 回了成功狀態。
- 發送端狀態：**已發送（sent，發送端觀察成功）**。

## 4. 接收端佐證
- `receipts.json` 缺失，log 也沒有接收端收據來源，因此無法標 confirmed。
- 同理，不能寫成「未送達」。sink 位址是本機 `127.0.0.1:63878`（`logs.jsonl:1`），但沒有它的紀錄可以對。
- 接收端狀態：**unknown**。

## 5. 設計文件的限制
- `design/design-review.md:3` 寫的行號已過期：「79 建通知、84 入列、88 日誌、89 回應」。目前是建通知 `Program.cs:82`、入列 `:88`、日誌 `:92`、回應 `:93`。本報告一律用現行行號。
- 文件第 7 點寫明本輪未跑 .NET，相關測試是待執行設計。本次結論只靠靜態閱讀與封存 log，沒有重現。
- 文件第 2 點提醒：接收端沒保存 refund_requested，不代表 payload 沒變。就算補到收據，也要另外比對 payload 內容。

## 6. 需補查的來源
1. `receipts.json`（fake sink 的收據）：有沒有 `7e746d20853d48b9b3948c1fe92319c1`，數量是否為 1，refund_requested 是否為 true。
2. 若沒有收據，要確認 sink 當時是否在執行，以及它有沒有寫檔或保存收據的設定。
3. 部署產物的 `VERSION` 檔或 `/version` 輸出，用來確認執行檔版本。

我沒有補送、沒有恢復資料，也沒有結案。

```json
{
  "order_id": "r2-healthy-01",
  "sender_status": "sent (notify_sent observed at data/logs.jsonl:3; notification_id 7e746d20853d48b9b3948c1fe92319c1)",
  "receiver_status": "unknown",
  "missing_sources": ["receipts.json"],
  "next_action": "由操作者提供 receipts.json（或 sink 端紀錄），核對 notification_id 是否恰好一筆且 refund_requested 一致；另提供 VERSION 或 /version 確認部署版本。在此之前不宣告已送達，也不補送、不結案。"
}
```