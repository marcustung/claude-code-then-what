**結論：最可能的根因是 carts，信心中等。**

資料範圍是 04:46:33 到約 05:10 UTC，基準只有約 14 分鐘。使用者回報的 05:01 其實比資料裡的實際異常時間晚。

**1. 異常時間線（metrics 的 istio-latency）**
- orders p90 在 04:58:45 從 0.049s 跳到 0.70s，之後穩定在約 0.95s。
- carts p90 在 04:58:47 從 0.06s 跳到 0.955s，之後穩定在約 2.26s。
- front-end p90 在 04:59:00 從 0.095s 跳到 0.75s，之後約 1.9s。
- carts p99 從 0.087s 升到 2.48s，約 28 倍。front-end p99 從 0.099s 升到 2.44s。
- user、catalogue 的 istio-latency 沒有同步跳升。payment 與 shipping 在 p90、p95 沒有變化。

**2. 資源指標**
- 事發後 5 分鐘對比基準，`front-end_container-sockets` 從 6.6 升到 19.7（+26.9σ），`carts_container-sockets` 從 19.6 升到 26.4（+10.9σ）。
- 兩者都是連線堆積的跡象：front-end 在等下游，carts 本身處理變慢。
- 各服務的 CPU 和記憶體沒有明顯變化，記憶體變動都在 1% 以內。
- carts-db 的記憶體只有輕微上升，從 7.70e7 到 7.77e7。我沒看到 carts-db 本身有異常。

**3. Log**
- 所有 log 的 `level` 欄位都是空的，`error` 欄位也沒有資料，所以只能用 message 關鍵字判斷。
- carts 的 log 量從 0.61 行/秒升到 1.15 行/秒。多出來的內容是 `UnknownHostException: zipkin` 的堆疊。
- 這個 zipkin 錯誤在 04:48:11 就已經出現（基準期），所以是背景雜訊，不是根因。
- queue-master 的 `AFUNIXSocketException ... unix://localhost:80` 從 04:46:33 就存在，也是基準期雜訊。
- front-end、user、orders 有 500/503 字樣的 log（例如 user 有 253 筆含 503）。我沒有逐筆確認它們是否集中在 04:58 之後。
- orders 的 log 在 04:58:20 前後仍顯示呼叫 payment 正常回應，耗時約 5ms。

**4. 排序理由**
- carts 的延遲升幅最大，而且 sockets 也跟著上升。
- orders 比 carts 早約 2 秒起跳，但時間解析度只有 1 秒，這個差距不能當作 orders 先出事的證據。
- orders 的延遲量級（約 1s）比 carts（約 2.3s）小，也可能是 orders 被 carts 拖慢後的結果。
- front-end 最晚起跳（04:59:00），符合它是下游受害者。
- payment 的 p99 統計分數雖高（185σ），但實際只從 0.00495s 到 0.00534s，沒有意義。
- shipping 的 p95 只從 0.0048s 到 0.0097s，仍在毫秒級，也沒有意義。

**不確定之處**
- 看不到 carts 內部的錯誤 log，所以不知道為什麼變慢。可能是 carts-db 的查詢變慢，也可能是 carts 的執行緒或連線池問題。
- orders 與 carts 誰先出問題無法分辨，因為起跳時間只差 2 秒。
- 基準只有 14 分鐘，統計 σ 的可信度有限。

```json
{"root_cause_service": "carts", "top3": ["carts", "orders", "carts-db"], "evidence": ["carts istio-latency-90: 0.06s -> 0.955s at 04:58:47, then ~2.26s; p99 0.087s -> 2.48s", "orders istio-latency-90: 0.049s -> 0.70s at 04:58:45, then ~0.95s", "front-end istio-latency-90 jumps at 04:59:00 (0.095s -> 0.75s -> ~1.9s), later than carts and orders", "front-end sockets 6.6 -> 19.7 (+26.9σ); carts sockets 19.6 -> 26.4 (+10.9σ)", "payment/shipping/user/catalogue show no meaningful latency change; CPU and memory change <1%", "carts zipkin UnknownHostException appears from 04:48:11 (baseline noise); queue-master AFUNIXSocketException appears from 04:46:33 (baseline noise)"], "uncertain": ["orders started only 2s before carts, at 1s resolution, so order is not established", "No internal carts error log was found, so the mechanism is unknown", "carts-db not shown abnormal, but a DB-side slowdown is not excluded", "Baseline is only ~14 minutes", "level and error fields are empty; the 500/503 logs were not checked by time"]}
```