## 結論
最可能的根因服務是 **checkoutservice**。證據如下，時間以事件回報的 01:05:00 UTC（epoch 1705626300，下稱 t0）為基準。

**1. checkoutservice 最早出現異常，比使用者回報時間早約 3 分鐘。**
- 約 t0−193 秒（約 01:01:47）起，`checkoutservice_container-cpu-usage-seconds-total` 從基準約 0.4 升到 11.45，之後多在 16～20。
- 同時間 `memory-working-set-bytes` 從約 1.3e7（13MB）升到 3.7e7，再到 1.55e8，t0−133 秒時約 2.68e8。事發後平均為 2.4e8，事發前平均為 4.3e7。
- `container-sockets` 從 9 升到 12，再升到 21。
- 事發前 baseline 的 CPU 與記憶體都很穩定，所以這是明顯的階躍變化。

**2. trace 顯示 checkoutservice 的 span 變慢。**
- 平均 duration 從正常時段的 14,075µs（n=3576）升到 t0−200～t0−5 秒的 109,638µs（n=1288），約 7.8 倍。事發後回到 14,213µs。
- frontendservice 同期從 11,257µs 升到 18,496µs，是被拖慢的下游症狀。
- currencyservice、emailservice、paymentservice、productcatalogservice、recommendationservice 都沒有明顯變化。例如 paymentservice 為 302µs → 196µs → 243µs。

**3. 之後出現連線失敗，與使用者看到的失敗一致。**
- frontend log 在 t0−5 秒（1705626295）出現 3 筆 error：`failed to complete the order: rpc error: code = Unavailable desc = upstream connect error or disconnect/reset before headers... delayed connect error: 111`。這是 frontend 呼叫下游下單時連線被拒。
- 同一時間點 `frontend_istio-error-total` 從 0 升到 0.2。`checkoutservice_container-network-receive-bytes-total` 平均從 2025 升到 7226（z≈15），表示請求在堆積。
- t0+21 秒起，checkoutservice 的 CPU 掉到 0.234 並維持不變。這與 checkoutservice 停止處理請求相符，但看起來是推論，不是直接觀察到的結果。

## 前 3 名候選
1. **checkoutservice**：CPU 與記憶體先暴衝，自身 span 變慢，之後下單失敗。
2. **frontend**：錯誤是在這裡被看到的，span 也變慢（11.3ms → 18.5ms）。但它是 checkoutservice 的上游，較像受害者。
3. **paymentservice**：`container-sockets` 從 3 升到 3.85，但事發前標準差為 0，所以 z 值被放大。它的 trace 延遲與 log 都正常（事發後仍有 `Transaction processed`）。把它排第 3 只是因為其他候選的證據更弱。

## 不確定之處
- 我沒有直接看到 checkoutservice 內部的原因，例如記憶體洩漏、無限迴圈或程式碼 bug。log 在異常期間沒有 error 或 warning，所以無法判斷是哪一種。
- 異常起點（約 01:01:47）比回報時間早，使用者感受到的失敗可能要等 01:04:55 的連線拒絕才出現。
- 全域統計中，三個 GKE 節點的 `node-cpu-seconds-total` 事發前後的 z 值很大（約 −100 到 −196）。它們是累計計數器，不是速率，所以我不採信，也沒有進一步檢查節點層級問題。
- redis 事發後沒有 log（事發前 15 筆）。量太小，我不認為是關鍵。
- 資料只覆蓋 t0 之後約 60 秒，無法確認 checkoutservice 是否後來恢復。

```json
{"root_cause_service": "checkoutservice", "top3": ["checkoutservice", "frontend", "paymentservice"], "evidence": ["checkoutservice cpu-usage-seconds-total 約 0.4 -> 11.45~20，起點約 t0-193s (01:01:47)", "checkoutservice memory-working-set 約 4.3e7 -> 2.4e8 (13MB -> 237MB 起於 t0-193s)；sockets 9 -> 12 -> 21", "trace: checkoutservice 平均 duration 14,075us -> 109,638us (t0-200~t0-5s)，事發後回到 14,213us；frontendservice 11,257 -> 18,496us", "frontend log t0-5s 三筆: failed to complete the order: rpc error: code = Unavailable ... delayed connect error: 111", "frontend_istio-error-total 0 -> 0.2；checkoutservice network-receive-bytes 2025 -> 7226 (z≈15)"], "uncertain": ["log 無 checkoutservice 內部 error，無法判斷是記憶體洩漏、CPU 迴圈或其他內部原因", "異常起點(01:01:47)早於回報時間(01:05)，且 t0 後只有約 60 秒資料", "t0+21s 起 checkoutservice CPU 降到 0.234 是否代表停止處理請求，只是推論", "paymentservice sockets 3 -> 3.85 因 baseline 標準差為 0 被放大，證據弱", "GKE 節點 cpu counter 的 z 值很大，但為累計計數器，未採信", "redis 事發後無 log，量太小，未能判斷"]}
```