**結論：** 新版慢情境的延遲主要來自通知排隊（約 2.19 秒），API 本身只花約 1.6 毫秒。下游呼叫約 0.27 秒。通知確實送達，而且接收端有獨立收據。

## 1. 新版是否有獨立接收證據

**觀察**
- Loki 在 `day24-fakesink-normal` 和 `day24-fakesink-slow` 各查到 9 筆 `notification_received`，各自 `notification_id` 不重複。
  - 正常情境：`after-normal-0` 到 `after-normal-8`，接收時間約 21:07:09Z。
  - 慢情境：`after-slow-0` 到 `after-slow-8`，接收時間 21:07:18.96Z 到 21:07:21.21Z，逐筆間隔約 0.27 秒。
- 這些收據由 fakesink 服務自己輸出，不是 API 的 `notify_sent` 計數。
- 串起一個完整事件（`after-slow-8`）：

| 項目 | 值 |
|---|---|
| notification_id | `60a97ad5a18b4728bf325826cf9cae8a` |
| request_id | `after-slow-after-slow-8` |
| trace_id | `c47c379ad7900380e5502f3095b1ec6e` |

  - API 端 log 有 `notify_enqueued`、`notify_worker_start`、`notify_sent` 和 `cancel`。
  - 接收端 log 有 `notification_received`，`received_at` 為 21:07:21.209Z。
  - 兩端的 `notification_id`、`request_id` 和 `trace_id` 一致。
- 兩個情境的 API 都在 Prometheus 記下 9 次排隊等待（`notification_queue_wait_milliseconds_count`），和 9 筆收據一致。

**推論**
- 慢情境的通知有送達，只是晚到。

**未知**
- 我沒有逐筆核對 API 端 `notify_enqueued` 是否剛好 9 筆。對帳式的另兩項（唯一成功轉換數、enqueued）只用 metrics 計數間接支持。
- 正常情境我沒有取 trace，只取了收據。

## 2. 慢情境單筆拆解（`after-slow-8`，以 Tempo 實際 trace 為準）

| 階段 | 耗時 | 來源 |
|---|---|---|
| API 取消 | 1.59 ms（log 為 0.7 ms） | 伺服器端 span `POST /orders/{id}/cancel`，回 200 |
| 排隊等待 | **2186.6 ms** | `notification.process` span 的 `queue.wait_ms`；log 的 `queue_depth` 為 8 |
| 下游呼叫 | 266.1 ms（client span） | 接收端 `POST /notify` span 為 258.8 ms |

- 取消在 21:07:18.759Z 結束，收據在 21:07:21.210Z，約 2.45 秒。
- 指標平均排隊等待：慢情境約 1119 ms（總和 10068 ms，9 筆），正常情境約 36 ms（總和 323 ms，9 筆）。這兩個數字假設指標只含該次執行。
- **推論：** 慢情境由單一 worker 依序送出，每筆約 0.27 秒，而且 9 筆幾乎同時入列，所以後面的通知排隊愈久。這是從程式（單一 worker、`Channel` 佇列）加 trace 時序推出來的，並非直接觀察到的因果。
- 原始碼中的 `OC_SINK_DELAY_MS` 可以解釋接收端變慢，但我沒有查到實際的環境設定，所以不確定。
- 「API 回 200」不能代表送達，API 的 span 在 1.6 ms 就結束了。

## 3. 新增觀測能回答什麼、前版缺什麼

**新版能回答**
- 同一事件跨 API、佇列、worker 和接收端的完整鏈路，靠 `notification_id`、`request_id` 和 `trace_id` 串起來。
- 延遲落在 API、排隊還是下游。
- 排隊延遲的分布（有指標，不用逐筆翻 log）。

**前版（未知）**
- 前版沒有集中匯出。我查了 21:06:42Z 到 21:07:03Z 的 Loki，沒有任何服務的 log，所以前版的 log、指標和 trace 都是「未知」，不是「沒執行」。
- 前版是否有排隊、延遲多少，都不能判斷。

**不宣稱**
- 我沒有量人工查案時間，所以不宣稱省時。

## 4. 資料來源錯誤演練

對 `missing-receiver-demo` 查 Log，gcx 回 `Datasource "missing-receiver-demo" not found`，exitCode 1，建議改跑 `gcx datasources list`。
- 我把它當資料來源錯誤，不當成「沒有 log」或「通知沒送出」，也沒有用它推論任何漏送。
- 它不影響上面的結論。

## 工具查詢失敗

- `gcx config view`：被權限擋下，沒執行。
- 一個用 Python 解析輸出的管線被權限擋下，沒執行，後來改用 gcx 內建的 `--jq`。
- 一個含 `IFS` 的指令被擋下，沒執行。
- 一個含 `${PIPESTATUS}` 的指令被擋下，沒執行，改為單純重跑。
- `missing-receiver-demo` 查詢失敗，是上面刻意演練的那次。
- 實際成功送出的查詢約 10 次，在 14 次上限內。

我沒有修改任何檔案。