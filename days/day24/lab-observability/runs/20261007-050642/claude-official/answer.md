新版兩個情境都有接收端的獨立收據。慢情境的延遲主要在佇列排隊和下游處理，不在取消 API。

## 1. 獨立接收證據（新版）
- **觀察：** Loki 的 `day24-fakesink-*` 有 `notification_received` 收據，來源是 `FakeSink/Program.cs` 的 `receipts.jsonl` 寫入點，不是 API 的 `notify_sent`。
- 正常情境（run_id `after-normal`）：9 筆 enqueued、9 筆 sent、9 筆收據，`received_at` 約 21:07:09.20～.25Z，落在 21:07:04～18Z 窗口內。
- 慢情境（`after-slow`）：9 筆 enqueued、9 筆 sent、9 筆收據，`received_at` 為 21:07:18.96～21:07:21.21Z，落在 21:07:17～31Z 窗口內。
- 串起同一事件的例子是 `after-slow-8`：
  - `request_id=after-slow-after-slow-8`、`notification_id=60a97ad5a18b4728bf325826cf9cae8a`、`trace_id=c47c379ad7900380e5502f3095b1ec6e`。
  - 這三個欄位在 API 的 `cancel`、`notify_enqueued`、`notify_worker_start`、`notify_sent` 和 sink 的 `notification_received` 都對得上。
  - 正常情境的 `after-normal-0` 到 `-8` 同樣能對上。
- 我只比對了 notification_id 的逐筆對應，沒有跑完整的去重對帳等式。

## 2. 慢情境拆解（`after-slow-8`，Tempo 實際 trace）
| 階段 | 耗時 | 依據 |
|---|---|---|
| API 伺服器 span（`POST /orders/{id}/cancel`） | 約 1.6 ms | span 起訖時間；log 的 `latency_ms=0.7` |
| 排隊（API 結束到 worker 開始） | 約 2185 ms | span 時間差；`queue.wait_ms=2186.6`；log 的 `queue_depth=8` |
| 下游呼叫（HTTP client span） | 約 266 ms | 其中 sink 伺服器 span 約 259 ms |
| 整體（API 結束到 sink 處理完） | 約 2451 ms | `received_at` 21:07:21.209Z |

- **觀察：** 前面的通知排隊時間逐筆遞增：1.97、307、580、882、1142、1403、1648、1919、2187 ms。收據間隔約 270 ms。
- **推論：** worker 一次只送一筆，每筆約 259 ms 的 sink 處理時間讓佇列越堆越長。這與 `FakeSink` 的 `OC_SINK_DELAY_MS` 和單一 worker 的程式吻合。
- Prometheus 的 `notification_queue_wait_milliseconds` 平均：慢情境約 1119 ms（10068/9），正常情境約 36 ms（323/9）。
- 回應 200 不代表送達：這筆 API 回應 1.6 ms 就完成，但收據在約 2.45 秒後才出現。

## 3. 新增觀測與前版缺口
- **新版現在能回答：**
  - 某筆通知在哪個階段花了多久（API、排隊、下游）。
  - 排隊時間是否逐筆上升。
  - 收據是否獨立到達，以及能否用 ID 對回 API 請求。
- **前版：** Loki 在 21:06:42～21:07:04Z 沒有任何 log（0 行）。前版沒有集中匯出，所以這個時段的 log、metrics、trace 查不到。
- **未知（不是「沒執行」）：** 前版正常與慢情境的排隊、下游耗時、送達狀況。前版的 21:06:42～21:07:05Z 我只查了 Loki 一次；Prometheus 和 Tempo 沒查，只因前版沒有集中匯出而推定查不到。
- 這次沒有量人工作時間，所以不宣稱省時。

## 4. 資料來源錯誤演練
- 對 `missing-receiver-demo` 做 Log 查詢，gcx 回報 `Datasource "missing-receiver-demo" not found`，結束碼 1，沒有回傳任何資料。
- 處理方式：這是查詢錯誤，不當成「0 筆 log」或「沒有事故」，也不拿來推論漏送。後續仍用正確的 `loki` 資料來源查證。

## 工具查詢失敗與限制
- `debug-with-grafana` Skill 在此環境不存在（`Unknown skill`），我改用 `gcx logs query --help` 和直接查詢摸索用法。
- `gcx --help` 因需核准未執行。
- 第一次 Loki 查詢的 `--jq` 格式錯誤（結束碼 2），改用 `-o raw` 重查。
- 故意查詢 `missing-receiver-demo` 失敗，屬預期。
- 已用 9 次 gcx 查詢（含 1 次失敗的 jq 和 1 次預期失敗），未超過 14 次。沒有修改任何檔案。
- 未知：慢情境的 sink 延遲實際設定值我沒讀到（只看到程式有此開關）；也未驗證完整的 enqueued = receipts 對帳等式。