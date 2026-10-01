# k6 上線前壓測：健康服務的自然承載上限

Day 17 用的實跑，跟 後續 明確區分開：後續 測「故障場景下抓不抓得到」（已注入的合成故障）；
這裡測**健康服務**在多少併發之後開始不對勁——逐步加壓，找 p95 跨過 後續 定的 250ms 門檻的那一點。

## 跑法

```powershell
# 1) 另開一個終端機，啟動服務（沿用既有的建置流程，讀取乾淨 baseline）
cd examples/order-cancel-lifecycle
dotnet build src/Api/Api.csproj -c Release -o bin/prelaunch
$env:ASPNETCORE_URLS = "http://127.0.0.1:5080"
dotnet bin/prelaunch/Api.dll

# 2) 本視窗執行壓測
k6 run k6/prelaunch-load.js --out json=k6/results/run-<timestamp>.json
```

## 讀什麼

`k6/results/run-*.json` 的 `Point` 事件，篩 `metric=="http_req_duration"` 依 `stage` 標籤分組看 p95；
或直接看 stdout 的 `checks`／`http_req_duration{expected_response:true}` 摘要與 threshold 是否 `✓`/`✗`。

## 界線

Windows 開發機、Kestrel 單程序、記憶體內儲存，數字是這台機器這次的結果，不是雲端生產環境的容量規劃；
沒有另外隔離 CPU／網路，跟同機其他負載共用資源。
