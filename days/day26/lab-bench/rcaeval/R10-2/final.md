**根因服務：`ts-route-service`**。證據顯示它在 12:48:04 UTC 被關閉、重啟，緊接著呼叫它的服務開始出現 503。不過 503 的目標是不是 route-service，我沒有直接確認。

資料時間基準：metrics 從 epoch 1733661162（12:32:42）開始。以下「+秒數」都是相對這個起點。

**證據**
1. **route-service 在事發時間被關閉再重建。** pod `…-gr58j` 在 +923s（12:48:04.906）出現 `Closing org.springframework.boot…`、`Stopping beans in phase 0`，並關閉 mongo 連線。在這之前它的 `RouteController: Route id` 請求日誌一直持續到 12:47:43 以後。
2. **新 pod 起不來，反覆出現同一個錯誤。** pod `…-n6bd9` 在 +927s 和 +959s 各印出一次：
   - `Error opening zip file or JAR manifest missing : /tmp/opentelemetry-javaagent.jar`
   - `agent library failed to init: instrument`
   - `Error occurred during initialization of VM`

   另一個 pod `…-szjk2` 在 +948s 才開始啟動，+989s 才印出 `Started RouteApplication in 45.09`，也就是約 70 秒的空窗。事發前 +907s 也出現過同樣的 JAR 錯誤，各 2 次，所以這個錯誤可能是舊問題。
3. **metrics 對得上這個時間點。**
   - `ts-route-service` 的 `spec-memory-limit-bytes`（734003200）和 `spec-cpu-quota`（50000）在 +924s 到 +930s 之間值遺失，+930s 後恢復，表示容器被重建。
   - `ts-route-mongo_container-sockets` 在 +929s 從 7 降到 2，之後 +977s 為 3、+996s 為 5。
4. **下游在重啟後約 2 秒開始出錯。** 第一筆錯誤落在 +923 到 +930s：
   - `ts-travel-service`：+925s 起出現 `HttpServerErrorException: 503 Service Unavailable`（24 次），另有 21 筆 `Servlet.service() … threw exception`。
   - `ts-travel2-service`：13 筆 503，+923s 起。
   - `ts-admin-travel-service`：15 筆 500，+927s 起。
   - `ts-food-service`：+938s 起有 500。
   - 這些 ERROR 在事發前都沒有出現。

**前 3 名候選**
1. `ts-route-service`：最早出現異常（+923s 關閉），且有容器重建、啟動失敗和 70 秒空窗。
2. `ts-route-mongo`：sockets 從 7 降到 2，隨 route-service 重啟而變。它較可能是被連動，不是原因。
3. `ts-travel-service`：錯誤最多，但出現在 route-service 關閉之後，我判斷它是受害者。

**不確定**
- 我沒有把 503 的呼叫目標對到 route-service。我只看到時間上緊接，沒有從 stack trace 或 trace 確認。
- 沒查到 route-service 為什麼被關閉。可能是 OOM、被縮減規格或人為重啟。memory limit 和 CPU quota 的值在重建前後都沒變。
- trace 的 `statusCode` 欄全是空的，各服務平均延遲在事發前後沒有明顯上升（route-service 3228→3251 µs）。所以無法用 trace 驗證錯誤傳播路徑。
- 只在 `ts-travel-mongo` 看到 `memory-failures-total` 有值（+1593s 以後），比事發晚約 11 分鐘。我認為它與初始事件無關，但沒有進一步驗證。
- 其他 mongo 的 `memory-cache` 微幅上升，我判斷是噪音。
- 很多 metrics 的事發前變異量接近 0，所以 z-score 不可靠，我只拿來找線索。

```json
{"root_cause_service": "ts-route-service", "top3": ["ts-route-service", "ts-route-mongo", "ts-travel-service"], "evidence": ["ts-route-service pod gr58j 於 12:48:04.906 (+923s) 出現 Closing context / Stopping beans 並關閉 mongo 連線", "新 pod 啟動失敗：Error opening zip file or JAR manifest missing : /tmp/opentelemetry-javaagent.jar（+927s、+959s 各 1 次，事發前 +907s 也有）；pod szjk2 於 +989s 才 Started（約 70 秒空窗）", "route-service spec-memory-limit-bytes(734003200) 與 spec-cpu-quota(50000) 在 +924~930s 值遺失後恢復，顯示容器被重建；route-mongo sockets +929s 7→2", "ts-travel-service +925s 起 24 筆 503 Service Unavailable、ts-travel2-service 13 筆、ts-admin-travel-service 15 筆 500、ts-food-service +938s 起 500，事發前皆無 ERROR"], "uncertain": ["未直接確認 503 的呼叫目標是 route-service", "route-service 被關閉的原因未知（OOM／縮規格／人為重啟）", "traces 的 statusCode 全空且平均延遲無明顯變化，無法驗證錯誤傳播", "travel-mongo memory-failures-total 在 +1593s 後才出現，與初始事件的關係未驗證", "metrics 事發前變異量接近 0，z-score 僅作線索"]}
```