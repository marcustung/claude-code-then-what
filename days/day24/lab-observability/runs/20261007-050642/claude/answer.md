# Day24 取消通知延遲調查

我用了 10 次工具查詢，上限是 14 次。沒有修改任何檔案。

## 1. 新版是否有獨立接收證據

**有。** 接收端 `day24-fakesink-*` 在 Loki 各有 9 筆 `notification_received`，order 編號 0 到 8。這是接收端自己寫的收據，不是 API 的 `notify_sent` 計數。程式也顯示收據由 FakeSink 在 `/notify` 處理時寫入（`src/FakeSink/Program.cs:23-40`）。

| 情境 | run_id | 接收筆數 | 接收時間（+08:00，換算 UTC 為 21:07:xx） |
|---|---|---|---|
| 新版正常 | after-normal | 9 | 05:07:09.20 到 09.25，約 50 ms 內全部到齊 |
| 新版慢 | after-slow | 9 | 05:07:18.96 到 21.21，間隔約 270 ms |

**串起同一事件（慢情境 after-slow-8）**，以 trace_id `c47c379ad7900380e5502f3095b1ec6e` 串連：

- **API 端：**
  - `notify_enqueued`，notification_id `60a97ad5a18b4728bf325826cf9cae8a`，order_id `after-slow-8`，request_id `after-slow-after-slow-8`，時間 05:07:18.758。
  - `cancel` 完成，`result=ok`，`transitioned=true`，`latency_ms=0.7`，`queue_depth=8`。
  - `notify_worker_start` 與 `notify_sent`，時間 05:07:20.94 與 05:07:21.21。
- **接收端：** `notification_received`，notification_id、order_id、request_id 與 API 端相同，`received_at` 為 05:07:21.209，來源是 `day24-fakesink-slow`。

正常情境用同樣的欄位對得上，例如 `after-normal-8` 對應 notification_id `59005fc8…`。

## 2. 慢情境拆解（after-slow-8）

讀取的是實際 Tempo trace，沒有拿 HTTP 200 當送達證據。

| 階段 | 耗時 | 依據 |
|---|---|---|
| API 請求 | **1.59 ms** | server span `POST /orders/{id}/cancel`，回 200 |
| 佇列等待 | **約 2187 ms** | `queue.wait_ms=2186.6`；入列 05:07:18.758，worker 在 05:07:20.945 開始處理 |
| 下游呼叫 | **約 266 ms** | HTTP client span 266.1 ms；接收端 `POST /notify` span 258.8 ms，且是 client span 的子 span |

`notification.process` 整體為 269 ms。

使用者感受到的延遲主要來自佇列：2187 ms 對 266 ms。接收端很慢，所以 worker 一筆一筆處理，後面的通知越排越久。

慢情境整體的佇列等待，我只能從 Prometheus 的 `notification_queue_wait_milliseconds` 看到分布：9 筆總和 10068 ms，平均約 1.1 秒，其中 5 筆落在 2500 ms 以內的桶。正常情境 9 筆總和 323 ms，其中 8 筆在 50 ms 以內，1 筆在 5 ms 以內。

## 3. 新增觀測後能回答什麼，前版缺什麼

**新版能回答：**
- 同一筆通知從 API、佇列、worker、HTTP 呼叫到接收端收據，能用 trace_id 和 notification_id 串起來。
- 延遲落在 API、排隊還是下游，可以分開看。
- 有獨立接收證據，不必靠服務自己的計數。

**前版缺什麼：**
- 前版沒有集中匯出，工具查不到。我查前版時段 21:06:42Z 到 21:07:03Z，得到空結果。
- 這只能表示「集中匯出裡沒有」。**前版的實際行為、通知是否送出、有多慢，我標為未知，不當成沒執行。**
- 前版如果有本機 `logs.jsonl` 或 `receipts.jsonl`，我沒讀，也不在授權範圍內。

我沒有量人工排查時間，所以**不宣稱省時**。

## 4. missing-receiver-demo 的錯誤演練

對 `missing-receiver-demo` 做 Log 查詢，工具回 `exit_code 1`，訊息是 `Datasource "missing-receiver-demo" not found`，建議先列出 datasources。`datasources` 清單裡確實沒有這個 uid。

處理方式：
- 把它記成**資料來源錯誤**，不是「查到零筆」，也不是「通知沒送」。
- 不拿它當送達或未送達的證據。
- 這不是另一個漏送事故。

## 觀察／推論／未知

**觀察**
- 新版正常與慢情境各有 9 筆接收端收據，且與 API 端 `notify_enqueued` 的 ID 對得上。
- after-slow-8 的 trace 顯示 API 1.59 ms、佇列約 2187 ms、下游約 266 ms。
- 慢情境收據間隔約 270 ms。
- 正常情境佇列等待總和 323 ms，慢情境 10068 ms。

**推論**
- 客訴型態（取消很快、通知較晚）符合佇列等待加上單線程消化慢速接收端。
- 這個推論來自 trace 和 log。程式上，worker 逐筆處理（`NotificationWorker.ExecuteAsync`），也與 `OC_SINK_DELAY_MS` 的設計相符。
- 我沒有直接讀到慢情境的 sink 延遲設定，所以這是推論。

**未知**
- 前版的送達情況與延遲。
- 我只完整拆解了 after-slow-8 這一筆，其他筆沒逐一拆。
- 沒查 `oc_*` 計數器，Prometheus 只查了佇列等待直方圖。
- 對帳等式「唯一成功轉換數 == enqueued == 收據數」我只對了收據數（9 對 9）。enqueued 與轉換數沒有逐項核對。

## 工具查詢失敗

1. **missing-receiver-demo 的 Log 查詢：** 刻意演練，datasource 不存在，結果如第 4 節。
2. **我自己的 Loki 查詢：** `count_over_time({service_name=~".+"}[1m])` 因基數超過 500 條 series 被拒。我改用 `sum by (service_name)` 後成功，但前版時段回空。
3. **第一次新版全量 log 查詢：** 輸出超過長度上限，被存到暫存檔。我沒有讀那個檔案，因為它在授權範圍外，改用較窄的查詢。