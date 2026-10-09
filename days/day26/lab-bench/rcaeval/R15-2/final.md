## 結論

最可能的根因是 **checkoutservice**。證據是它的記憶體暴增，且延遲只出現在它發出的呼叫上。

**資料範圍**：metrics 涵蓋 00:49:17–01:06:00 UTC，事發前只有約 12 分鐘基準，事發後只有數分鐘。

**證據**

1. **checkoutservice 記憶體暴增（事發後 z-score 約 2.5）**
   - rss 從約 11.4–11.9 MB 的穩定值，在 t+780 秒（約 01:02:17）起跳到 15–26 MB。
   - 事發前後平均 rss 為 40.3 MB → 222.8 MB，working set 為 42.1 MB → 226.5 MB。
   - sockets 從 9 升到 12，最後一筆是 21，事發前後平均為 9.5 → 15.9。
   - 同時間其他服務的記憶體都沒有這種變化。emailservice 的 rss 為 40.89 MB → 40.91 MB，幾乎沒變。
2. **checkoutservice 的 istio 延遲在同一時點跳升**
   - latency-90 從約 0.2 秒變成 2.05–2.25 秒，在 t+780 秒的樣本跳升。
   - latency-50 為 0.20 → 0.78 秒。
3. **trace 顯示慢在 checkoutservice 自己的呼叫**
   - 以 30 秒為一格取中位數，事發前（約 01:00–01:01:30）對比事發後（約 01:01:30–01:04）：

   | 呼叫 | 事發前（ms） | 事發後（ms） |
   |---|---|---|
   | checkout→GetCart | 4.4 | 79.2 |
   | PlaceOrder（checkoutservice） | 81.4 | 311.2 |
   | PlaceOrder（frontend 視角） | 84.9 | 852.4 |

   - GetCart 這條只在 checkoutservice 呼叫端變慢。
   - 最後一個 30 秒格的 GetCart 中位數達到 99.8 ms，且整段 GetCart 的平均值約是事發前的 62 倍。
   - 下游的 paymentservice Charge（0.2 → 0.2 ms）、emailservice（0.3 → 0.3 ms）、productcatalogservice 都沒變慢。
4. **症狀往上游傳到 frontend**
   - frontend 在 1705626295（約 01:04:55）有 3 筆 error log，路徑都是 `/cart/checkout`：`failed to complete the order: rpc error: code = Unavailable desc = upstream connect error or disconnect/reset before headers... remote connection failure`。
   - frontend 的 latency-99 為 0.52 → 1.35 秒，frontend istio-error-total 最後一筆為 0.2。
   - 只有結帳流程（PlaceOrder）受影響，其他頁面操作沒變慢。frontend 的 GetProduct、ListProducts 中位數事發前後約 2.5 → 2.6 ms、2.9 → 3.0 ms。

**時間點**：從 trace 看，PlaceOrder 的 10 秒格中位數在 01:01:20 前後（約 40–90 ms）開始明顯變高，01:01:30–01:05 之間偶有 1–2 秒的尖峰。這比使用者回報的 01:04 早約 2–3 分鐘，錯誤要到 01:04:55 才出現在 log。

## 前 3 名候選
1. **checkoutservice**：記憶體 5 倍、latency-90 約 10 倍、PlaceOrder 延遲最先且最大幅上升。
2. **cartservice**：checkoutservice→GetCart 變慢，但 frontend 自己呼叫的 GetCart 沒變（中位數 4.2 → 4.2 ms）。cartservice 的 istio latency-90 也只是 4.79 → 4.91 ms，所以較不像根因。
3. **redis**：它是 cartservice 的後端，但 memory rss 為 2.631 → 2.626 MB，沒有異常，列為排除性的候補。

## 不確定之處
- trace 裡沒有 cartservice 的 server span。我無法直接判斷 GetCart 變慢是 cartservice 的問題，還是 checkoutservice 本身的資源問題，只能靠 frontend 的 GetCart 沒變來間接排除。
- 事發後資料太短，沒有足夠樣本確認記憶體是持續洩漏還是一次性暴增。
- 3 筆 error log 太少，統計意義有限。
- 我沒有直接看到 checkoutservice 的程式或應用層 log 說明記憶體為何上升。

```json
{"root_cause_service": "checkoutservice", "top3": ["checkoutservice", "cartservice", "redis"], "evidence": ["checkoutservice rss 約11.7MB 穩定，於 t+780s(約01:02:17) 起升至15-26MB；事發前後平均 rss 40.3MB→222.8MB", "checkoutservice istio latency-90 約0.2s→2.05-2.25s，同一時點跳升", "trace: checkoutservice→GetCart 中位數 4.4ms→79.2ms；PlaceOrder 81.4→311.2ms（frontend視角 84.9→852.4ms）", "paymentservice Charge 0.2→0.2ms、emailservice 0.3→0.3ms，下游未變慢", "frontend 在 1705626295 有3筆 /cart/checkout error: rpc error code=Unavailable upstream connect error", "frontend GetCart 中位數 4.2→4.2ms 且 cartservice latency-90 4.79→4.91ms，不像 cartservice 本身出問題"], "uncertain": ["trace 沒有 cartservice server span，無法直接排除 cartservice/redis", "事發後資料僅數分鐘，無法判斷記憶體是洩漏或一次性暴增", "error log 僅3筆", "無 checkoutservice 應用層 log 說明記憶體上升原因", "trace 顯示的異常起點(約01:01:20-01:02:17)早於使用者回報的01:04"]}
```