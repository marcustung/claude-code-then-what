# 通知契約 v2.1（新需求，2026-09-21 起草；作者尚未接受前標「提案」）

> 這是 **新增** 的需求，v1 與準備中的 v2 都沒有包含通知。不能把它寫成早已確認的條件。
> 狀態：`proposed`。作者接受後改 `accepted` 並填日期；`decisions-v2.1.md` 記錄接受或修改。

## 為什麼需要它

取消功能通過測試（v1 三綠、v2 七個場景），使用者卻沒收到取消通知——開發時的完成條件只到「狀態改了」，沒有到「對方知道了」。這一段要把「完成」往後延一格，並讓它可被獨立核對。

## 契約

| 編號 | 規則 | 說明 |
|---|---|---|
| NC-01 | **每一次實際發生的狀態轉換（Cancelled false→true）產生恰好一則通知** | 通知的分母是「唯一成功轉換」，不是 API 呼叫次數 |
| NC-02 | **重複取消不產生新通知** | 已取消再取消：API 回 200／ok=false 或 409（見 API），不入通知佇列 |
| NC-03 | 已出貨拒絕取消：不產生通知 | 失敗的轉換沒有通知 |
| NC-04 | 三個層次分開：**API 接受**（HTTP 2xx 且 `transitioned=true`）≠ **狀態已改**（GET 回 Cancelled=true）≠ **通知送達**（接收端有收據） | 服務自己的 `notify_sent_total` 不算送達證據；送達以**接收端的收據**為準 |
| NC-05 | 通知失敗要重試，重試有上限（預設 3 次、退避 200／400／800 ms）；超過上限進 `dead_letter`，記 log，**不得安靜丟失** | dead_letter 是待人工處理清單，不是成功 |
| NC-06 | 每則通知帶 `notification_id`（唯一）、`order_id`、`request_id`、`run_id`（若呼叫方有帶） | 讓接收端收據能對回 API request 與 run |
| NC-07 | 服務啟動時輸出 `version`；每筆 log 帶 `version` | 版本可追溯 |

## 觀測欄位（供後續對帳）

- 服務 `logs.jsonl`：每 request 一行（`request_id`、`run_id`、`order_id`、`op`、`result`、`transitioned`、`latency_ms`、`queue_depth`、`version`）
- 服務 `/metrics`：`oc_cancel_requests_total{result}`、`oc_transitions_total`、`oc_notify_enqueued_total`、`oc_notify_sent_total`、`oc_notify_failed_total`、`oc_notify_dead_letter_total`、`oc_notify_queue_depth`
- 接收端 `receipts.jsonl`：每則**實際收到**的通知一行（`notification_id`、`order_id`、`request_id`、`run_id`、`received_at`）——**獨立來源**，不是服務計數器的拷貝
- 對帳等式：`唯一成功轉換數 == enqueued == receipts 行數（去重 notification_id）`；任何一邊不等即 FAIL

## 明確不做

- 不接真實郵件／簡訊／付款；`RefundRequested` 只是業務結果旗標。
- 儲存在程序記憶體，**不保證重啟持久性**；要證明 crash recovery 才補持久化與對應測試。
- 權限使用測試身分（`X-Actor` header），不代表正式認證設計。
