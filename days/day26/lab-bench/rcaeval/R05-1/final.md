**結論：根因最可能是 `orders` 服務。** 它在 09:09 左右重啟，之後 front-end 的錯誤才出現。重啟原因我在資料裡找不到。

**我做了什麼**
- `traces.csv` 只有標題列，沒有資料，所以完全沒用到呼叫鏈。
- 結論來自 `logs.csv`（143,826 行）和 `metrics.csv`（1,441 筆，每秒一筆）。
- metrics 的 time 欄是 epoch 秒，不是 HH:MM。09:12 UTC 是 1732353120。

**證據**
1. **orders 在 09:09 前後換了 pod。**
   - logs 裡 orders 有兩個 pod 名：`orders-7fff6698cb-rlq5k` 和 `orders-8d7957d74-2gvb7`。
   - 舊 pod 最後一筆正常 log 是 09:09:02。
   - 09:09:41 出現 `main ... Starting service Tomcat`，09:10:31 出現 `Starting beans in phase`。這是 Spring Boot 冷啟動。
   - orders 的 `container-cpu-usage-seconds-total` 事前約 1，之後最高到 46.3（啟動尖峰）。
   - orders 的 `istio-latency-95` 從 0.048 升到 1.226。
2. **orders 在 09:09:09 連不上 orders-db。**
   - log：`MongoSocketOpenException ... Caused by: java.net.ConnectException: Connection refused`，目標是 `orders-db:27017`。
   - orders-db 這邊在 09:09:08.988 有三筆 `Connection ended`，來源是 127.0.0.6。這符合 orders 端被砍掉而斷線。
   - orders-db 本身正常：Checkpointer log 每分鐘都有，直到 09:20。記憶體約 71 MB 且平穩。CPU 沒有異常上升。
3. **front-end 的錯誤跟在 orders 之後。**
   - 09:10 的 log：`statusCode":503 ... upstream connect error ... Connection refused`。
   - `front-end_istio-error-total` 平均從 0.517 升到 2.05。`orders_istio-error-total` 從 0.507 升到 2.05，兩者幾乎同步。
   - orders 的 `Exception` 類 log 逐分鐘數量：09:09 有 3 筆，09:10 有 128 筆，09:11 到 09:20 每分鐘約 240 到 260 筆。
4. **payment、shipping、carts、user、catalogue 沒有受影響。**
   - 09:09 之後它們沒有任何 exception 或 refused 類 log（各為 0）。
   - payment 和 shipping 的 `istio-request-total` 下降（1.79→0.067、1.62→0.067），應該是 orders 不再呼叫它們。

**要排除的雜訊（事發前就有）**
- front-end 的 `Payment declined: amount exceeds 100.00`（406）從 08:57 就有，約每 3 分鐘 8 到 16 筆。這是業務規則，不是故障。
- queue-master 的 `AFUNIXSocketException ... unix://localhost:80: No such file or directory` 從 08:56 就在，事發前就已大量出現（08:5x 有 660 筆）。這是長期的設定問題。

**不確定的部分**
- orders 為什麼重啟，我找不到證據。記憶體穩定在約 339 MB，沒有 OOM 跡象。可能是人為重啟、部署，或外部注入的故障。
- 重啟在 09:09，比回報的 09:12 早約 3 分鐘。使用者感受到的時間可能落後於實際故障時間。
- 我沒有檢查 orders 節點層級的資源，也沒有 K8s event，所以無法確認重啟的直接觸發點。
- 09:12 之後 orders 仍有每分鐘約 240 多筆 exception，我只讀了前幾筆（Mongo 連線錯誤）。我沒有確認這段時間內的錯誤型態是否一致，也不知道它何時恢復。
- 第 2、3 名是依「受影響的先後」排序，不是各自有獨立證據。

```json
{"root_cause_service": "orders", "top3": ["orders", "front-end", "orders-db"], "evidence": ["orders 的 pod 由 orders-7fff6698cb-rlq5k 換成 orders-8d7957d74-2gvb7；舊 pod 最後正常 log 在 09:09:02，09:09:41 起出現 Tomcat/Spring 冷啟動 log", "09:09:09 orders log: MongoSocketOpenException / Connection refused 連 orders-db:27017；orders-db 同時在 09:09:08.988 記錄 3 筆 Connection ended，且 orders-db 的 Checkpointer log 持續到 09:20、記憶體約 71MB 平穩", "front-end 09:10 出現 503 upstream connect error ... Connection refused；front-end_istio-error-total 0.517→2.05，orders_istio-error-total 0.507→2.05", "orders cpu-usage-seconds-total 事前約 1，之後最高 46.3；istio-latency-95 0.048→1.226；orders exception 數 09:09=3、09:10=128、09:11 起每分鐘約 240-260", "payment、shipping、carts、user、catalogue 在 09:09 之後沒有 exception/refused 類 log；payment、shipping 的 istio-request-total 下降到約 0.067"], "uncertain": ["orders 重啟的原因未知（記憶體穩定約 339MB，無 OOM 證據）", "重啟（約 09:09）早於回報的 09:12，約 3 分鐘", "traces.csv 只有標題列、無資料，沒有呼叫鏈佐證", "沒有 K8s event 與節點資源資料", "09:12 之後 orders 每分鐘約 240 多筆 exception 的錯誤型態只看了前幾筆，也不知何時恢復", "第 2、3 名只是依受影響順序排列，沒有獨立證據"]}
```