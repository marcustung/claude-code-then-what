**根因：adservice（可信度高，但無法確認 adservice 內部原因）**

**1. 唯一明顯的使用者端錯誤是 frontend 呼叫 AdService/GetAds 失敗**
- trace：11:34 之後，frontend 的錯誤 span 有 2043 個，其中 2042 個是 `hipstershop.AdService/GetAds`，statusCode 12.0（gRPC UNIMPLEMENTED）。事發前 frontend 錯誤 span 為 87。
- log：`frontend` 出現 2042 筆 `failed to retrieve ads`，時間範圍 11:33 到 11:45，數量與 trace 一致。
- metrics：`frontend_istio-error-total` 事發前為 0，事發後平均 0.001。我只看到一個樣本 0.067（約 11:35），數字很小，只能當輔助證據。

**2. adservice 自己的訊號最早出現，且在 frontend 錯誤之前**
- log：adservice 最後一筆 log 在 11:33，內容是 `Ad Service started, listening on 9555`，代表它重啟過。之後 adservice 完全沒有 log，事發前則有 2192 筆，多為 `received ad request (...)`。
- trace：整份 traces.csv 沒有 adservice 的 span。
- metrics：約 11:34 起 `adservice_container-network-receive-packets-total` 從約 7 掉到沒有值，我看到的樣本是空值。事發前後平均從 6.86 降到 2.92（4.0 個標準差），是所有指標中偏離最明顯的一批。
- 記憶體：`adservice_container-memory-rss` 從約 88 MB 升到約 159–163 MB，之後降到約 75 MB。這符合重啟或重新載入，但我沒有確認原因。

**3. 其他服務在事發前後沒有明顯變化**
- trace 平均耗時：checkoutservice 6711→6299、currencyservice 112→91、productcatalogservice 38→36、recommendationservice 2520→2461，都沒有變差。
- 其他服務的 log 量與基準相近。
- 只有 1 筆 paymentservice `UnacceptedCreditCard`（visa_electron），屬於單一的業務錯誤，與本次事件無關。

**前 3 名候選**
1. **adservice**：重啟後不再收流量，GetAds 持續失敗，最先異常。
2. **frontend**：錯誤全部出現在它身上，但這是受害者。它自己的 log 只有 `failed to retrieve ads`，沒有其他錯誤。
3. **shippingservice**：`shippingservice_istio-latency-99` 的偏離有 14.4 個標準差，但數值幾乎沒變（0.005→0.005），標準差大只是因為基準太平穩。這是我最不確定的一項，沒有其他證據支持它。

**不確定之處**
- adservice 為何重啟（OOM、crash 或部署）。資料裡沒有 k8s 事件，也沒有它崩潰前的錯誤 log。
- 記憶體尖峰是重啟的原因還是結果，我無法分辨。
- status 12 通常表示「方法未實作」，也可能是服務在啟動中尚未註冊，我只能判斷它符合服務還沒準備好。
- 錯誤到 11:45 結束，但 adservice 一直沒有恢復 log，也沒有 span。我不確定它是否真的恢復，還是 frontend 改成不再呼叫它。
- metrics 的 time 欄是 epoch 秒，logs 和 traces 是 HH:MM，我用 1732275240 對應 11:34 切分，約有 1 分鐘誤差。

```json
{"root_cause_service": "adservice", "top3": ["adservice", "frontend", "shippingservice"], "evidence": ["frontend 在 11:34 後有 2042 筆 AdService/GetAds 失敗 span，statusCode 12.0；log 有 2042 筆 'failed to retrieve ads'（11:33-11:45）", "adservice 最後一筆 log 在 11:33，內容為 'Ad Service started, listening on 9555'，之後沒有任何 log（事發前 2192 筆），traces 中也沒有 adservice span", "adservice_container-network-receive-packets-total 事發前平均 6.86、事發後 2.92（4.0 個標準差），約 11:34 起出現空值", "adservice memory-rss 約 88MB 升到約 160MB，之後降到約 75MB", "其他服務 trace 平均耗時與 log 量與基準相近，只有 1 筆無關的 paymentservice UnacceptedCreditCard"], "uncertain": ["adservice 重啟的原因（OOM、crash 或部署）沒有 k8s 事件可以確認", "記憶體尖峰是重啟的原因還是結果", "status 12 的確切含意", "錯誤 11:45 之後停止，但 adservice 沒有 log 也沒有 span，無法確認是否真的恢復", "metrics 用 epoch 對應 11:34，約有 1 分鐘誤差", "shippingservice 排第三，只是統計上的偏離，沒有其他證據"]}
```