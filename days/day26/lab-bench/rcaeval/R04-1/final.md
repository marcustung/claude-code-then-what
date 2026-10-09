**根因服務：adservice。** 它的 NullPointerException 出現在使用者回報時間點，frontend 的錯誤隨後跟著出現。

**我做的分析**
- 事發時間以 04:52 UTC（epoch 約 1731905520）為界，把資料分成事前和事後比較。
- 指標用事前平均與標準差算偏移量（z-score）。
- traces 和 logs 則看各服務的錯誤與延遲。

**證據**
1. **adservice 的 log 有例外，事前沒有。**
   - 事後出現 1741 筆 `java.lang.NullPointerException: Cannot invoke "java.util.Collection.toArray()" because "<p…`，以及 1741 筆 `SEVERE: Exception while executing runnable io.grpc.internal.ServerImpl$JumpToApplicationTh…`。
   - 第一筆 NPE 的時間戳是 1731905521，也就是 04:52:01，與回報時間吻合。
   - 最後一筆是 1731906223，也就是 NPE 持續約 700 秒。
   - 事前沒有任何 NPE。事前 adservice 只有兩筆 "temporarily unavailable" 啟動訊息（Stats enabled / Tracing enabled），看起來是無害的啟動訊息。
2. **adservice 的 istio 指標在事後轉差。**
   - `adservice_istio-error-total` 從 0 升到 0.0142，z-score 約 1.4×10⁷，這是所有欄位中偏移最大的之一（0 基準讓 z 值被放大）。
   - `adservice_istio-latency-95` 從 0.0059 升到 0.0131，約 2.2 倍，z-score 約 4.4。
3. **frontend 的錯誤是下游症狀。**
   - `failed to retrieve ads` 事前只有 17 筆，事後 1746 筆。
   - frontend 的 trace 錯誤數從 17 升到 1746。其中 statusCode 2.0 共 1740 筆，與 adservice 的 1741 筆 NPE 幾乎一一對應。
   - 其他服務（productcatalog、currency、recommendation、checkout、payment、email）的 trace 錯誤數為 0。
   - 這些服務的平均延遲事前事後也沒有明顯變化，例如 productcatalog 31→30 µs，currency 109→109。

**前 3 名候選**
1. **adservice**：最先出現錯誤，錯誤數與下游 1:1 對應。
2. **frontend**：錯誤數最多（1746），但它是呼叫端，錯誤訊息是 "failed to retrieve ads"，指向 adservice。我把它視為受害者而非根因。
3. **emailservice 或 paymentservice**：只有網路接收量微增（emailservice 267→575，paymentservice 277→542 bytes/s）。兩者的 trace 都沒有錯誤，我認為是雜訊或流量變化，不是根因。

**不確定之處**
- traces 裡沒有 adservice 自己的 span，serviceName 只出現 7 個服務。我無法用 trace 直接確認 adservice 的延遲，只能靠 log 和 istio 指標。
- trace 的 statusCode 為空的有 7702 筆，我沒有深入分析它們。
- 我沒有查出 NPE 的直接觸發原因，例如設定變更或資料問題。log 只顯示 `Collection.toArray()` 收到 null，我沒有看到原始碼或部署紀錄。
- 節點磁碟讀取指標（`node-disk-read-bytes-total` 0→17.4）的 z-score 很大。但數值本身極小，基準全是 0，我判斷是統計假象。
- 事前窗口只有約 13 分鐘，基準偏短。

```json
{"root_cause_service": "adservice", "top3": ["adservice", "frontend", "emailservice"], "evidence": ["adservice log: 事後 1741 筆 java.lang.NullPointerException (Collection.toArray() on null)，事前 0 筆，首筆 04:52:01 UTC", "frontend 'failed to retrieve ads' 事前 17 → 事後 1746；frontend trace 錯誤 17 → 1746（statusCode 2.0 共 1740 筆）", "adservice_istio-error-total 0 → 0.0142；adservice_istio-latency-95 0.0059 → 0.0131 (約 2.2 倍)", "其他服務 trace 錯誤為 0，平均延遲無明顯變化（productcatalog 31→30，currency 109→109）"], "uncertain": ["traces 中沒有 adservice 的 span，無法用 trace 直接確認其延遲", "NPE 的觸發原因（設定、資料或程式）無法從資料確認", "trace 中 statusCode 為空的 7702 筆未分析", "emailservice/paymentservice 網路接收量微增，原因不明，可能是雜訊", "事前基準窗口只有約 13 分鐘"]}
```