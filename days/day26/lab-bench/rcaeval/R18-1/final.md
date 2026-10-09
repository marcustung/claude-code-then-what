我剛才在核對 carts 的 CPU 飆升時間和 carts-db 的慢查詢是不是新出現的。核對完了,結論如下。

## 分析結果

**時間基準**:metrics 的 time 是 epoch 秒,02:57 UTC 等於 1705633020。資料範圍是 1705632217 到 1705633657,共 1441 筆。

**1. carts 是最先異常的服務(最可能的根因)**
- `carts_container-cpu-usage-seconds-total` 事發前平均約 9.2。
- 事發後平均約 48.3,z 約 3.3。
- 逐 10 秒看:1705632950 是 11.5,970 是 30.0,1000 是 49.8。之後一直停在約 50。
- 開始上升的時間是 02:56:10,比回報時間早約 50 秒。
- 上升後 CPU 平了,看起來像打滿上限。
- `carts_container-cpu-system-seconds-total` 從 2.57 升到 34.7(z 約 4.4)。
- `carts_container-memory-cache` 從 4.5 萬升到 2,260,992 bytes,變化時間和 CPU 同一段。
- carts log 有 `UnknownHostException: zipkin` 和 `Dropped N spans`,共 50 筆。最早在 1705632237,事發前就有,所以是背景噪音,不是根因。

**2. carts-db 是次要嫌疑**
- log 有 4646 筆 MongoDB `Slow query`,全來自 carts-db。
- 典型內容是 `planSummary":"COLLSCAN"`、`docsExamined":36678`。耗時中位數 207 ms,最大 1304 ms。
- 其中 2546 筆發生在事發前(最早 1705632219),所以慢查詢不是新出現的。
- 不能因此說 carts-db 是起點。我也沒有量化事發後慢查詢有沒有增加。
- carts-db 的 memory-cache 只上升約 2%(8.93e7 到 9.10e7),幅度很小。

**3. queue-master 屬於背景噪音,可能是干擾項**
- 有大量 `RetryExec I/O exception` 共 3516 筆,以及 `DockerSpawner Exception trying to launch` 共 1172 筆。
- 這些在資料第一秒(1705632217)就出現,事發前已存在,不能解釋 02:57 的變化。
- `queue-master_container-memory-failures-total` 的取樣值從 0.32 變成 3.6。在 1705633657 這一個取樣點是 148。我只看到最後一點才暴增,所以不能當成起點。

**其他觀察**
- payment 的 `memory-failures-total` 事發後出現約 0.0435(z 很大)。但事發前基準是 0,絕對值極小。在 1705633212 才開始變動,晚於 carts,所以可能只是結果。
- 節點 `disk-read-bytes-total` 在 `nw9c` 和 `3px7` 兩個節點出現 z 極大的值。它們的事發前基準都是 0,所以 z 被放大了。第一次變動在 1705633153,晚於 carts,絕對值也小(約 273 B/s)。
- `catalogue_istio-latency-95` 從 0.00498 升到 0.00703,z 約 4.3。幅度小,我不確定是否相關。
- 各服務 log 事發前後的筆數都是正常比例(例如 front-end 25355 筆對 20278 筆),沒有明顯的錯誤或重試風暴。

## 不確定之處
- 資料裡沒有 front-end 或 carts 的請求延遲與錯誤率,所以「使用者操作變慢」只能用 CPU 打滿間接推論。
- 我沒有找到 carts CPU 上升的直接原因(例如流量暴增或程式迴圈),只能說它是時間上最早的異常。
- carts 的 CPU 起點比回報時間早約 50 秒。我認為合理,因為使用者感受到變慢會晚於資源飽和,但這是推測。
- carts-db 的 COLLSCAN 慢查詢是長期存在的,它可能是 carts 負載高的背景因素,但我無法證明因果。
- payment 排在第三是依時間順序和 z 值判斷,證據偏弱。

```json
{"root_cause_service": "carts", "top3": ["carts", "carts-db", "payment"], "evidence": ["carts cpu-usage-seconds-total 事發前均值約 9.2,事發後約 48.3;1705632950 為 11.5,1705632970 為 30.0,1705633000 起約 50(02:56:10 開始上升,早於回報時間)", "carts cpu-system-seconds-total 2.57 升到 34.7;memory-cache 4.5 萬升到 2,260,992 bytes", "carts-db 有 4646 筆 Slow query,內容為 COLLSCAN、docsExamined 36678,耗時中位數 207 ms、最大 1304 ms,但其中 2546 筆在事發前就已存在", "payment memory-failures-total 在 1705633212 才從 0 變為約 0.0435,時間晚於 carts"], "uncertain": ["沒有請求延遲或錯誤率資料可直接驗證使用者症狀", "未找到 carts CPU 上升的直接原因,只確定它時間上最早", "carts-db 慢查詢事發前就存在,沒有量化事發後是否增加,因果不明", "queue-master 的 I/O exception 與 DockerSpawner 錯誤事發前已存在,視為噪音;其 memory-failures 只在最後一個取樣點暴增", "payment 排名第三證據偏弱,節點 disk-read 的 z 值被事發前基準為 0 放大"]}
```