## 結論

最可能的根因服務是 **user**。user-db 排第二,因為我看不出慢的是 user 本身,還是它背後的 user-db。

事件時間軸以 metrics 為準。metrics 的 time 是 epoch 秒,範圍是 20:11:53 到 20:35:53。

### 證據

1. **user 的延遲最先惡化,而且最嚴重。**
   - `user_istio-latency-95` 在 20:24:00 還是 0.0097。
   - 到 20:24:30 變成 0.098,20:25:00 變成 0.362,之後穩定在約 0.5。基準值是 0.0096。
   - 這大約是基準的 50 倍。
   - 事件回報寫 20:26,但我看到的實際起點是 20:24:30,比回報早約 2 分鐘。

2. **其他服務的延遲都在 user 之後或同時上升,幅度較小。**
   - front-end p95 從 0.090 升到 0.216(20:24:30),20:26 為 0.415。
   - orders p95 從 0.049 升到 0.182(20:24:30)。
   - catalogue 的 p95 約 0.005→0.007,carts 約 0.024→0.03,payment 維持 0.005。這三個服務幾乎沒變。
   - 這些服務與 user 在同一個 30 秒取樣點一起變化,所以 metrics 本身分不出先後。
   - front-end 和 orders 是否因為呼叫 user 才變慢,是我的推測,資料沒有直接證實。

3. **user 自己的 log 顯示處理時間在 20:24 暴增。**
   - 20:22 時 GetUsers 平均 took=2.19ms,max 10ms。
   - 20:24 時 GetUsers 平均 46.9ms,max 1024ms。
   - 同一時間 PostAddress 平均從約 4ms 升到 170ms,Register 從約 2ms 升到 50ms。
   - Health 也變慢,20:24 平均 31.7ms,max 638ms。連 Health 都慢,代表不只是某個 API 的問題。

4. **連線數跟著暴增。**
   - `user_container-sockets` 從 15 升到 32,升了約 2 倍。
   - user-db 的 log 在 20:24:19 到 20:24:48 出現 #8 到 #13 的新連線(「13 connections now open」)。
   - `user-db_container-sockets` 的平均值從 7 升到 16。
   - 我沒有看到任何 user-db 的 error log。

5. **下面這些是事前就有的雜訊,不是根因。**
   - queue-master 在 20:11 起就持續報 `AFUNIXSocketException ... /var/run/docker.sock`,事發前後都有。
   - carts 一直報 `UnknownHostException: zipkin`,同樣事發前就有。

### 前 3 名候選

1. **user**:延遲最先、最大幅度上升,而且 log 裡的 took 也證實變慢。
2. **user-db**:連線數與記憶體同步增加,可能是 user 慢的真正原因。它的 memory-rss 約 34.7MB→36.3MB,只是小幅增加。
3. **front-end**:它是入口,p95 從 0.09 升到 0.4。它的症狀很明顯,但我判斷它是被拖慢的一方。

### 不確定的部分

- 我分不出慢的是 user 本身,還是 user-db 的查詢變慢拖累 user。user-db 沒有慢查詢 log。
- metrics 是 30 秒間隔,user 和 front-end/orders 的啟動時間差在同一個取樣點內,無法確定誰先。
- 我沒有分析 user 的 CPU 與記憶體,所以不知道是不是資源飽和造成的。
- 我只是把事發前後做平均值比較,沒有做完整的因果分析。

```json
{"root_cause_service": "user", "top3": ["user", "user-db", "front-end"], "evidence": ["user_istio-latency-95: 0.0097 (20:24:00) -> 0.098 (20:24:30) -> 0.362 (20:25:00), 基準 0.0096", "user log GetUsers took 平均 2.19ms/max 10ms (20:22) -> 46.9ms/max 1024ms (20:24); PostAddress 4ms -> 170ms", "user_container-sockets 15 -> 32; user-db sockets 7 -> 16; user-db log 20:24:19-48 新增連線 #8-#13", "front-end p95 0.09 -> 0.216 (20:24:30)、orders p95 0.049 -> 0.182,與 user 同一取樣點上升; catalogue/payment 幾乎不變", "queue-master docker.sock 與 carts zipkin 錯誤自 20:11 起就存在,屬事前雜訊"], "uncertain": ["無法區分 user 本身慢或 user-db 拖慢 user(user-db 無 error/慢查詢 log)", "metrics 為 30 秒取樣,user 與 front-end/orders 的先後無法分辨", "未分析 user 的 CPU/記憶體,不知是否資源飽和", "front-end/orders 因呼叫 user 而變慢只是推測"]}
```