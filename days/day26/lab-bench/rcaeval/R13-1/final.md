## 結論

**最可能的根因是 `recommendationservice`。** 它在 23:51 前後開始變慢,比使用者回報的 23:54 早約 3 分鐘。

## 證據

**1. 延遲從 23:51 開始跳升。** 我把 `recommendationservice` 的 span 按分鐘統計(以 23:54:00 為 0,單位 µs)。

| 時間 | p50 | p95 |
|---|---|---|
| 事發前 (-240s) | 3363 | 5253 |
| 23:51 (-180s) | 4658 | **100140** |
| 之後各分鐘 | 約 4300–4800 | 約 99000–101000 |

- 事發前 p95 一直在 4.5–5.3 ms。
- 23:51 起 p95 固定在約 100 ms,最大值到 0.9 s。
- p95 是「正常值 → 約 100 ms」的台階式變化,不是逐漸惡化。這種固定的 100 ms 看起來像某種固定延遲或逾時,不像負載造成。

**2. 變慢的是 `recommendationservice` 自己對 productcatalog 的呼叫,不是 productcatalog 本身。**
- `recommendationservice` 的 `ListProducts` client span:p95 4373 → **98272**。
- 對應的 `productcatalogservice` server span:p95 27 → 28,幾乎沒變。
- 慢 trace 的例子:`ListRecommendations` 100681 → client 端 `ListProducts` 99293 → productcatalog server 端只有 **3 µs**。
- 所以延遲出現在 `recommendationservice` 內部,或它到 productcatalog 之間的網路或 sidecar。服務端本身沒有變慢。

**3. 症狀往上游傳到 frontend。**
- `frontend → ListRecommendations` p50:7424 → **50314**;p95:10298 → 184867。
- `frontend` 的整體 `frontend` span p50:44798 → **95113**;p95:171523 → 250078。這就是使用者感受到的「變慢」。

**4. 其他服務沒有劣化。**
- 沒變的:`productcatalogservice`(p50 12 → 12)、`currencyservice`(p50 134 → 134)、`paymentservice`、`emailservice`。
- `AdService/GetAds` p95 4539 → 4972,`CartService/GetCart` p95 6342 → 7290,沒有明顯劣化。
- 所有 trace 的 statusCode 都沒有出現非 0 的錯誤碼,所以是變慢,不是失敗。

## 前三名候選

1. **`recommendationservice`**:最先劣化,延遲只出現在它的出站呼叫上。
2. **`frontend`**:受害者。它的延遲是從 `ListRecommendations` 傳上來的,但它自己的其他下游呼叫都正常。排第二只是因為它確實有症狀,不是因為我認為它是根因。
3. **`productcatalogservice`**:`recommendationservice` 慢的那段呼叫指向它,所以列入。但它的 server span 完全正常,可能性很低。

## 不確定之處

- **logs 幾乎沒有幫助。** 所有 log 都沒有 error 或 warn 等級,只有 info、debug 和空值。我沒有在 log 裡找到任何直接證據。
- **metrics 也沒有指出具體原因。** 以事發前的標準差為基準,偏離超過 3σ 的欄位裡,沒有 `recommendationservice` 的 CPU、記憶體或網路。
  - 有偏離的欄位:節點磁碟讀取(`cx8g` 與 `xte3` 兩個節點)、`emailservice` 的網路接收(812 → 1194)、`frontend` 的 istio-latency-95。
  - 我沒有深入追節點磁碟讀取和 `emailservice` 網路,不確定它們是否相關。它們可能是巧合,也可能是更上層的原因。
- **無法判斷固定 100 ms 延遲的機制。** 可能是 `recommendationservice` 到 productcatalog 之間的網路或 sidecar 問題,也可能是 `recommendationservice` 自身的問題(例如 DNS、連線重建、`recommendationservice` 的 pod 資源限制)。這點需要更多資料才能確認。
- **時間差的解讀。** 我認定 23:51 是起點,比使用者回報早 3 分鐘,這是依 trace 資料判斷的。使用者可能是延遲累積到明顯後才察覺。

```json
{"root_cause_service": "recommendationservice", "top3": ["recommendationservice", "frontend", "productcatalogservice"], "evidence": ["recommendationservice span p95 從約 5253µs 在 23:51 跳到約 100140µs,之後持續約 99000–101000µs", "recommendationservice 的 ListProducts client span p95 4373→98272µs,但 productcatalogservice server span p95 27→28µs,慢 trace 範例 client 99293µs 對應 server 3µs", "frontend ListRecommendations p50 7424→50314µs、p95 10298→184867µs;frontend 整體 span p50 44798→95113µs", "productcatalogservice、currencyservice、paymentservice、emailservice 的 p50 沒變,所有 trace 無非 0 statusCode"], "uncertain": ["logs 沒有 error/warn 等級,沒有直接證據", "metrics 沒有 recommendationservice 的顯著異常,無法判斷具體機制(網路、sidecar 或 pod 本身)", "節點磁碟讀取與 emailservice 網路接收的偏離是否相關未追查", "trace 顯示 23:51 起劣化,早於回報的 23:54,是否為使用者察覺延遲所致為推測"]}
```