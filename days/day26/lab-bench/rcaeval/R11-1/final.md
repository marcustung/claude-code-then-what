**結論：最可能的根因是 `currencyservice`。**信心中等，原因見最後的不確定處。

**1. 最先、最明顯的異常出現在 CurrencyService 的呼叫延遲（traces）**
以 2024-01-19 22:10 UTC（epoch 1705702200）切開比較前後的平均 duration：

| 呼叫 | 事發前 | 事發後 | 倍數 |
|---|---|---|---|
| frontend → `CurrencyService/GetSupportedCurrencies` | 50.9 ms | 207.5 ms | 4.07× |
| frontend → `CurrencyService/Convert` | 51.2 ms | 207.3 ms | 4.05× |
| checkout → `CurrencyService/Convert` | 55.0 ms | 207.4 ms | 3.77× |
| `frontend` 整體 | 183.8 ms | 638.8 ms | 3.48× |
| `PlaceOrder`（checkout） | 217 ms | 702 ms | 3.2× |

- 其他下游服務幾乎沒變，例如 `ProductCatalog/GetProduct` 13→14 µs、`PaymentService/Charge` 232→259 µs、`EmailService/SendOrderConfirmation` 278→296 µs。
- `frontend` 和 `PlaceOrder` 變慢的幅度，跟 Currency 呼叫增加的延遲（約 +156 ms）大致吻合。這表示它們是被拖慢的，不是源頭。

**2. currencyservice 自己的 metrics 也在事發時跳變**
- `currencyservice_istio-latency-95` 從約 0.07–0.08 跳到 0.24，之後維持在 0.24。
- `currencyservice_container-memory-failures-total` 在 1705702170（22:09:30）就偏離基準，z≈6。基準平均約 477，之後最高 1118。
- `currencyservice_istio-bytes-95` 在 1705702141 超過 5σ，但數值只從 1.6 變成 1.634，幅度很小。
- currencyservice 的 CPU 累計值在事發後下降（約 37→15→9.6），同時 `spec-cpu-quota` 固定為 50000。
- 這代表服務在事發後處理量變少，同時延遲變高。
- log 筆數也符合：currencyservice 事發前 35145 筆、事發後 10689 筆，約 3.3:1。其他服務多為約 2:1，例如 adservice 6665:3475、frontend debug 36632:19291。

**3. 其他服務的異常出現較晚或幅度小，較像受害者**
- `checkoutservice` 的 network-receive-bytes 在 22:11:50（1705702310）才異常（z≈17），晚於 currencyservice 的異常。
- `frontend` 的 memory 和 sockets 有小幅偏離。memory-rss 從 15.9 MB 到 17.2 MB，sockets 從 29 到 31。
- `paymentservice`、`cartservice`、`adservice` 的網路和 CPU 偏離都不大。

**4. log 沒有直接證據**
- 所有服務的 level 欄只有 info、debug 或空值，沒有 error 或 warn。
- traces 的 statusCode 幾乎都是 `0.0`。
- 所以根因判斷只靠延遲和 metrics，沒有錯誤訊息可引用。

**不確定之處**
- currencyservice 自己的 server span 事發後反而變短（Convert 484→187 µs）。client 看到的 +156 ms 發生在 server span 之外。
- 因此也可能是 currencyservice 的網路、sidecar 或排程延遲，或 CPU 受限（quota 50000，約 0.5 core），而不是程式邏輯變慢。我無法從現有資料區分這幾種。
- `frontend_container-sockets` 的 z 值是 2e9，因為事發前基準的標準差接近 0。這個數字只代表「基準幾乎不變」，不要當成嚴重程度。
- 第 2、3 名只是依受影響程度排序，沒有證明因果。

```json
{"root_cause_service": "currencyservice", "top3": ["currencyservice", "frontend", "checkoutservice"], "evidence": ["trace: frontend->CurrencyService/Convert 平均 51.2ms -> 207.3ms (4.05x)；GetSupportedCurrencies 50.9ms -> 207.5ms；checkout->Convert 55.0ms -> 207.4ms", "其他下游無明顯變化：ProductCatalog/GetProduct 13->14us、Payment/Charge 232->259us、Email/SendOrderConfirmation 278->296us", "frontend 整體 183.8ms -> 638.8ms (3.48x)，PlaceOrder 217ms -> 702ms (3.2x)，與 Currency 呼叫增加的延遲量級吻合", "currencyservice_istio-latency-95 約 0.07-0.08 -> 0.24；memory-failures-total 在 22:09:30 先偏離基準 (z≈6，477 -> 最高 1118)", "currencyservice log 事發前/後 35145/10689 (約 3.3:1)，其他服務約 2:1，顯示處理量下降", "checkoutservice network-receive-bytes 在 22:11:50 才異常 (z≈17)，晚於 currencyservice"], "uncertain": ["log 沒有 error/warn，statusCode 幾乎都是 0.0，無直接錯誤證據", "currencyservice server span 事發後反而變短 (Convert 484->187us)，client 看到的延遲在 server span 之外，可能是網路/sidecar/CPU 配額，無法與服務內部問題區分", "frontend 與 checkoutservice 的排名只依受影響程度，未證明因果", "frontend_container-sockets 的 z=2e9 只是基準標準差接近 0 的人為結果"]}
```