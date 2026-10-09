## 結論

最可能的根因是 **carts**，但它和 carts-db 之間的因果方向我無法完全確定。

## 時間線（metrics 的 t=0 是 12:30:40 UTC）

1. **基準期 12:31–12:41**
   - queue-master 每分鐘約 190–300 筆 `AFUNIXSocketException ... /var/run/docker.sock`。
   - 這類錯誤在事發前就一直存在，我判斷是環境本身的雜訊，不是這次事件的原因。
   - front-end 每分鐘有 6–18 筆錯誤，多為 `Not Acceptable` 的 PaymentDeclined 之類。
2. **12:42:46** orders 開始大量記錄 `HttpServerErrorException: 503 Service Unavailable`。
   - 每分鐘筆數：12:42 有 9、12:43 有 64、12:44 有 38。
   - front-end 同步出現 `Order response ... Internal Server Error ... IllegalStateException "Unable to create or..."`，筆數與 orders 完全相同（9、64、38），所以它是下游症狀。
3. **12:42:51** carts-db 的 conn1–conn14 在同一毫秒內全部 `Connection ended`，這是 15 條連線一起斷。
4. **12:42:56** carts 記錄 `MongoSocketOpenException ... Connection refused`，連不到 `carts-db:27017`。
5. **12:43:46** carts 重新啟動：
   - 出現 main thread 的 `Cluster created with settings {hosts=[carts-db:27017]`。
   - 出現一長串 `Mapped ...` 啟動 log。
   - 12:44:01 到 12:44:15 之間 carts 有 14.2 秒沒有任何 log。
   - carts-db 在 12:43:46 之後開始接受新連線。
6. **carts 的 metrics**
   - memory-usage 從約 332 MB 升到約 568 MB（t=780s），再到約 673 MB（t=1020s），之後降回約 342 MB。
   - 事發前後的 memory-cache 從 8.1e5 升到 3.9e6。
   - CPU 在重啟附近從約 5 升到約 28–30（累計值每分鐘的變化量）。
   - 以事發前標準差換算，carts memory-cache 偏離 386σ，memory-usage 偏離 31σ，是所有指標中偏離最大的。
   - carts-db 的記憶體只小幅增加，從 7.88e7 到 8.51e7，沒有重啟跡象。

## 判斷

- 所有症狀都沿著 orders → carts 這條路徑傳播：orders 回 503、front-end 回 500。
- carts 是 metrics 偏離最明顯、並且有重啟痕跡的服務。

## 不確定之處

- 12:42:46 orders 的 503 比 12:42:51 carts-db 斷線早 5 秒。這代表 carts 可能先出問題，也可能是 orders 呼叫的別的服務先失敗。
- 我沒有看到 orders 503 的目標服務名稱，只是推測它是 carts。
- carts-db 的 mongod 沒有重啟（Checkpointer 每 60 秒照常記錄）。15 條連線同時中斷，可能是 carts 端先掛掉或被重啟，也可能是 carts-db 的網路層出了問題。
- carts 重啟的原因（OOM 或其他）沒有直接證據。
- 在 12:30 附近，orders 與 front-end 已有 28 筆錯誤、carts 有 18 筆，包含一筆 `ConcurrentModificationException`。這些是資料開頭的啟動期錯誤，我當作雜訊，但不確定。
- 任務說的 12:44 起點，比我看到的 12:42:46 晚。使用者回報可能有延遲。

```json
{"root_cause_service": "carts", "top3": ["carts", "carts-db", "orders"], "evidence": ["12:42:46 orders 開始出現 HttpServerErrorException 503 Service Unavailable（12:42:9筆、12:43:64筆、12:44:38筆），front-end 的 Internal Server Error 筆數完全相同（9/64/38）", "12:42:51 carts-db conn1–conn14 同一毫秒 Connection ended；12:42:56 carts 記錄 MongoSocketOpenException Connection refused 連 carts-db:27017", "12:43:46 carts 重啟（main thread 出現 Cluster created 與 Mapped 啟動 log，12:44:01–12:44:15 有 14.2 秒無 log）", "carts memory-usage 約 332MB → 約 568MB（t=780s）→ 約 673MB，memory-cache 8.1e5 → 3.9e6，偏離基準 386σ；carts-db 記憶體僅 7.88e7 → 8.51e7"], "uncertain": ["orders 503 比 carts-db 斷線早 5 秒，且未確認 503 的目標服務", "carts-db 的 mongod 沒有重啟，15 條連線同時中斷是 carts 端造成還是 carts-db 網路問題不明", "carts 重啟原因（如 OOM）無直接證據", "queue-master 的 docker.sock 錯誤在事發前就存在，視為雜訊但未完全排除", "12:30 附近的啟動期錯誤是否與本次事件有關不明"]}
```