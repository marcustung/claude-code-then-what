**根因服務最可能是 `emailservice`**，但證據只來自 metrics，log 和 trace 都沒有直接的錯誤紀錄。

事發時間以 05:32 UTC（epoch 1705728720）為界，前 815 秒為基準，後 626 秒為事發期。

**證據**
- **CPU 暴增**：`emailservice_container-cpu-usage-seconds-total` 在基準期約 0.28–0.34，在 T-35 秒的取樣點已是 19.67，T+25 秒為 19.71，持續到約 T+265 秒（11.75）。T+325 秒回到 0.30。
- **延遲同步變高**：`emailservice_istio-latency-95` 從 0.0048 升到 0.0992（約 20 倍），期間同樣回落到 0.0048。
- **連線與記憶體**：`emailservice_container-sockets` 從 3 升到 10，T+325 秒之後仍維持 9。working-set 記憶體從 43.5MB 升到約 55.7MB，之後只回落到約 49MB。
- **統計排名**：用事發前的標準差標準化後，變化最大的是 paymentservice 記憶體（z=3.9）、emailservice 記憶體 rss（3.1）和 emailservice sockets（2.9）。emailservice 的 CPU 因為只持續約 5 分鐘，被後段平均稀釋，整體 z 只有約 1.2–1.3。
- **trace**：`emailservice` 的平均 span 耗時從 806 增加到 1501，是各服務中唯一明顯變動的。`SendOrderConfirmation` 的 p95 從 698 增加到 808，p50 不變（281）。
- **下游影響**：`checkoutservice_istio-latency-99` 從 0.32 平均升到 0.45（z=1.4）。`checkoutservice` 呼叫 EmailService 的 p95 是 84758 → 80333，沒有變慢。

**其他候選**
- **`checkoutservice`**：它是 emailservice 的呼叫端，`PlaceOrder` p50 從 100931 增加到 105432，約 4%，幅度很小。它更像是受害者，不是起因。
- **`paymentservice`**：記憶體 working-set 從 34.19MB 升到 35.43MB（+3.6%），統計上顯著（z=3.9），但幅度很小。trace 的 `Charge` p95 從 488 增加到 577，p50 不變，我認為是雜訊。

**不確定之處**
- logs.csv 的 level 只有 info、debug 和空值，沒有 error 或 warn。`error` 欄位也完全沒有值，因此 log 無法佐證。
- traces 的 statusCode 全部正常，沒有失敗的 span。使用者回報的「失敗」在資料裡看不到。
- 我只以整體 CPU 的跳升判斷 emailservice 最先出事，沒有逐秒確認它比其他服務早幾秒。取樣點顯示它在 T-95 到 T-35 秒之間起變化，早於 05:32。
- email 的 CPU 暴增後，下游變慢的幅度很小，因此與使用者感受到的「操作變慢」之間的因果鏈只是推論。
- `adservice` 的記憶體 z=2.9 和 `cartservice` 的 memory-failures 從 1.7 升到 3.9，都沒有深入查。
- 我的統計只比較了事發前後的平均，沒有做更細的時序變點偵測。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "paymentservice"], "evidence": ["emailservice CPU usage 約 0.3 → 19.7，持續約 5 分鐘後回到 0.30", "emailservice istio-latency-95 0.0048 → 0.0992，約 20 倍", "emailservice sockets 3 → 10，working-set 記憶體 43.5MB → 55.7MB", "traces 中 emailservice 平均 span 耗時 806 → 1501，SendOrderConfirmation p95 698 → 808", "checkoutservice istio-latency-99 0.32 → 0.45，PlaceOrder p50 100931 → 105432", "paymentservice working-set 記憶體 34.19MB → 35.43MB (z=3.9)，幅度小"], "uncertain": ["logs 沒有 error/warn 等級，error 欄位為空；traces 無失敗 statusCode，無直接錯誤證據", "未逐秒確認 emailservice 是否比其他服務更早異常，只知道在 T-95 到 T-35 秒之間起變化", "emailservice 到使用者可見變慢的因果鏈只是推論，下游變慢幅度很小", "adservice 記憶體與 cartservice memory-failures 的變化未深入查"]}
```