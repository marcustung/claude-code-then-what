我已經找到延遲的起點，分析可以收尾了。

## 分析結果

**時間線**:資料涵蓋 21:54:52–22:18:52 UTC。currencyservice 延遲在 **1705702020 前後(約 22:07:00–22:07:30 UTC)** 突然跳升,比使用者回報的 22:10 早約 3 分鐘。

**1. currencyservice(根因,信心中高)**
- traces:`frontendservice → CurrencyService/Convert` 的 30 秒中位延遲,在 1705701990 時段為 5.8 ms,到 1705702020 時段變成 **204.8 ms**,之後固定在約 205 ms。
- `GetSupportedCurrencies` 的 p50 從 5.8 ms 變成 205.1 ms。`checkoutservice → Convert` 從 5.7 ms 變成 204.9 ms。
- metrics `currencyservice_istio-latency-50` 約在 t=1705702062–72 之間從 0.004–0.008 s 跳到 0.097 s,之後約 0.10 s。p99 從 0.096 s 變成 0.25–0.35 s。
- currencyservice 自己的 server span 只有約 0.1 ms,前後沒變。所以延遲出現在 currencyservice 處理邏輯之外,可能在它的 sidecar、網路或 CPU 排程。這一點我沒有直接證據確認。
- CPU 與流量:`currencyservice cpu-usage` 事發前平均 33.09,事發後 26.51;`network-receive-packets` 從 162 降到 114。這比較像是請求被拖慢後吞吐下降,不像資源飽和。
- 規格:它的 cpu quota 是 50000,是所有服務中最大的,所以不像是被限流。
- logs:currencyservice 只有 info,內容是 `conversion request successful`,沒有 error。每分鐘 log 量從約 2300 降到約 2000–2100。

**2. frontend(受害者,第 2 名)**
- `frontend_istio-latency-50` 從 0.114 s 變成 0.420 s(z=2.3),p99 從 0.84 s 變成 2.42 s。
- traces:`frontend` 根 span 的中位延遲從 50.6 ms 變成 443 ms,p95 變成 2075 ms。這與每次頁面載入呼叫 Convert 多次、各加 200 ms 相符。
- `frontend_container-sockets` 從 29 增加到 30.2,可能是請求排隊造成。

**3. checkoutservice(受害者,第 3 名)**
- `PlaceOrder` 中位延遲從 99.9 ms 變成 644 ms。
- 它內部的 `Convert` 呼叫也各增加約 200 ms。
- `checkoutservice_istio-latency-50` 從 0.188 s 變成 0.633 s。

**排除項**
- productcatalogservice、recommendationservice、payment 的 span 延遲都沒變(例如 `ListRecommendations` 為 3.8 ms,前後相同)。
- cartservice、redis 的 trace 與 log 都沒有異常。redis 的 log 只有例行 RDB 儲存。
- 所有 `statusCode` 都是 0.0,沒有看到失敗請求。使用者說的「失敗」我沒有在資料中找到證據,只看到變慢。

## 不確定之處
- 時間差:最早的 trace 跳升在 22:07 左右,使用者回報是 22:10。我認為使用者回報晚了,但沒有其他資料可以交叉驗證。
- 精確的 +200 ms 很整齊,像是被注入的延遲或 timeout 類行為,不像資源耗盡。我無法判斷延遲是在 currencyservice 本身、它的 istio sidecar 還是網路。
- 沒有 error log,所以沒有直接的錯誤訊息可以指向根因機制。
- 前後的 metrics 比較用的是固定切點 22:10,而實際起點是 22:07,所以 z 值會被稀釋。

```json
{"root_cause_service": "currencyservice", "top3": ["currencyservice", "frontend", "checkoutservice"], "evidence": ["trace: frontend->CurrencyService/Convert 30s 中位延遲在 1705702020 前後從 5.8ms 跳到 204.8ms,之後固定約 205ms", "trace: GetSupportedCurrencies p50 5.8ms -> 205.1ms; checkout->Convert 5.7ms -> 204.9ms", "metrics: currencyservice_istio-latency-50 約 t=1705702062-72 從 0.004-0.008s 跳到 0.097s,p99 0.096->0.25-0.35s", "currencyservice 自身 server span 約 0.1ms 不變,log 只有 info,無 error", "下游症狀: frontend 根 span 中位 50.6ms->443ms, PlaceOrder 99.9ms->644ms", "productcatalog/recommendation/payment 的 span 延遲前後無變化"], "uncertain": ["延遲位置在 currencyservice 內部、sidecar 或網路無法分辨", "最早跳升約 22:07,與回報的 22:10 有約 3 分鐘落差", "資料中沒有失敗請求(statusCode 皆 0.0),只有變慢", "沒有 error log 可說明根因機制", "精確 +200ms 像注入的延遲,但無法確認"]}
```