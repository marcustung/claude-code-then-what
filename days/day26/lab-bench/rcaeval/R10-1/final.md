**根因服務：ts-route-service。** 這是 12:48 的一次滾動更新出了問題，只有部分把握，下面分開說。

## 證據

**1. route-service 在 12:48 重新部署，期間完全斷線。**
- 舊 pod `ts-route-service-6f78466fb7-gr58j` 最後一筆 log 在 12:48:04（"Clo…" mongodb 連線關閉）。
- 新 pod `…-szjk2` 於 12:48:08 開始啟動，12:49:10 才出現 `Started RouteApplication in 45.099 seconds`。
- traces 中 route-service 的 `GET /routeservice/routes/{routeId}` 以每 10 秒計：
  - 12:48:00 前約 30–65 筆。
  - 12:48:00 起連續 6 個區間（約 60 秒）是 0 筆。
  - 之後在 12:49:20 前後恢復到 40–75 筆。
- 這段空窗和使用者回報的 12:49 開始變慢或失敗大致吻合。

**2. 下游呼叫方在 12:48 出現 503。**
- `ts-travel-service` 出現 `HttpServerErrorException: 503 Service Unavailable`，第一筆在 12:48:20。
- 含 503 的 log 每分鐘筆數：12:48 有 34 筆，12:49 有 15 筆。之前每分鐘只有 0–3 筆。
- `ts-travel2-service` 的 503 在 12:48 有 23 筆，之前每分鐘 1–4 筆。
- `ts-admin-travel-service` 也有 ERROR 類 log，事發後只有 8 筆，事發前 22 筆。
- ERROR 的 log 內容只寫了 503，沒有寫是呼叫哪個服務，所以 503 來自 route-service 是推論，不是直接看到。

**3. 同一個 route-service ReplicaSet 還有新版 pod 一直起不來。**
- `ts-route-service-6bdc49b787-n6bd9` 從 12:47:49 起反覆出現三行錯誤：
  - `Error opening zip file or JAR manifest missing : /tmp/opentelemetry-javaagent.jar`
  - `Error occurred during initialization of VM`
  - `agent library failed to init: instrument`
- 重複時間點：12:47、12:48、12:49、12:51、12:54、12:59，間隔越來越長，符合 CrashLoopBackOff。
- 這個新版 pod 看起來是 OpenTelemetry agent 注入失敗，就是 12:48 滾動更新的觸發事件。
- 我只看到這些 log，沒有 k8s 事件或 deployment 設定，無法確認是誰改了什麼。

## 前三名候選
1. **ts-route-service**：有重啟、請求量歸零約 60 秒、新版 pod 反覆崩潰。
2. **ts-travel-service**：503 數量最明顯（12:48 有 34 筆），但它是 route-service 的呼叫方，比較像受害者。
3. **ts-travel2-service**：503 的數量和時間點與 travel-service 相似，同樣是受害者。

## 不確定之處
- metrics 在事發前後沒有明顯異常。變化最大的欄位幾乎都是原本接近 0 的計數器（例如 `ts-user-service … memory-failures-total` 0→0.034），我判斷是雜訊，沒有採用。
- traces 的 `statusCode` 全是空值，無法算錯誤率。事發後各 operation 延遲也大多沒變。最大的是 `ts-food-service GET` 11.3→14.8 ms（1.3 倍），route-service 的 `GET` 是 4.6→5.8 ms（1.2 倍）。
- 事發後 `ts-preserve-other-service` 的 log 在 12:50 有 83 筆，其他分鐘約 28 筆。我沒有看內容，不確定是否相關。
- route-service 的症狀只維持約 1 到 2 分鐘，使用者「持續變慢」的感受可能還有別的原因。我只看到新版 pod 仍在崩潰，沒有證據顯示它影響流量。

```json
{"root_cause_service": "ts-route-service", "top3": ["ts-route-service", "ts-travel-service", "ts-travel2-service"], "evidence": ["route-service 舊 pod 12:48:04 後無 log，新 pod 12:49:10 才 Started (45.1s)", "traces: route-service GET routes/{routeId} 在 12:48:00 起約 60 秒內每 10 秒 0 筆，之前 30–65 筆", "travel-service 12:48:20 起 HttpServerErrorException 503，12:48 有 34 筆 (之前每分鐘 0–3)", "travel2-service 12:48 有 23 筆 503 (之前每分鐘 1–4)", "route-service ReplicaSet 6bdc49b787 的 pod 反覆 'Error opening zip file or JAR manifest missing : /tmp/opentelemetry-javaagent.jar' / 'Error occurred during initialization of VM'，12:47–12:59 重複出現"], "uncertain": ["503 的 log 沒寫呼叫目標，來自 route-service 為推論", "metrics 無明顯異常，變動多為近零計數器雜訊", "traces statusCode 全為空，無法算錯誤率", "沒有 k8s 事件或 deployment 設定，無法確認滾動更新的原因", "ts-preserve-other-service 12:50 的 log 量增加 (83 筆) 未查明", "route-service 症狀僅約 1–2 分鐘，與使用者回報的持續變慢是否完全對應不確定"]}
```