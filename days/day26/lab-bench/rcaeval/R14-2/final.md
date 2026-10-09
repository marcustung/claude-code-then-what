## 結論

最可能的根因是 **emailservice**。它的 istio 延遲、記憶體和 socket 都在事發後明顯惡化，而且下游的 checkoutservice 明確回報呼叫它失敗。

## 證據

**1. emailservice 的指標在事發後明顯偏離基準**

事發點取 09:28 UTC。下表比較事發前與事發後的平均值，z 值是偏離基準的標準差倍數。

| 指標 | 事發前 | 事發後 | z 值 |
|---|---|---|---|
| istio-latency-90 | 0.0047 | 0.253 | 624 |
| istio-latency-99 | 0.0118 | 1.679 | 46.6 |
| istio-latency-95 | 0.0087 | 0.639 | 26.8 |
| container-sockets | 3.02 | 6.88 | 16 |
| memory-working-set-bytes | 4.35e7 | 9.63e7 | 15.2 |
| network-receive-packets | 5.8 | 14.0 | 6.3 |

- 這是全部指標裡偏離最大的一組服務。
- 它的 p50 延遲幾乎沒變（0.0030 到 0.0046）。這代表是尾端延遲變差，不是整體變慢。
- 記憶體約增為 2.2 倍，socket 數約增為 2.3 倍。

**2. 下游 checkoutservice 的 log 直接指向 emailservice**
- checkoutservice 在 09:26:39（資料起點後 746 秒）出現第一筆 warning：`failed to send order confirmation to "someone@example.com": rpc error: code = Unavailable desc = no healthy upstream`。
- 這類 warning 共 10 筆，另有 1 筆 trace 錯誤。事發前 trace 錯誤為 1 筆，事發後為 9 筆。
- 在整份 log 裡，checkoutservice 只有這一種非 info 的訊息，其他服務沒有類似的錯誤。
- 這個「no healthy upstream」錯誤來自寄送訂單確認信，也就是呼叫 emailservice 的那一步。這是我從訊息內容推斷的，log 沒有直接寫出目標服務名稱。

**3. checkoutservice 是被拖累的症狀**
- checkoutservice 的 istio-latency-95 從 0.242 升到 1.001（z=23.5），latency-99 從 0.306 升到 1.902（z=10.3）。
- 它的 trace p95 從 78,136 升到 123,949（單位依資料原樣，我沒有換算）。
- 它的 p50 幾乎不變（4070 到 4122）。
- 時序上 emailservice 先出問題，checkoutservice 才跟著出現錯誤與延遲。

**4. 其他服務沒有明顯異常**
- currencyservice、productcatalogservice、frontend、recommendationservice 的 trace 中位數與 p95 事發前後幾乎一致。例如 frontend 中位數是 3655 到 3694，p95 是 62508 到 63731。
- adservice、recommendationservice、frontend 的 log 裡 level 非 info 的筆數很多，但內容是 debug 與 INFO 的一般訊息，不是錯誤。這是我的 level 篩選太粗造成的，不能當作異常證據。

## 前 3 名候選

1. **emailservice**：指標偏離最大，而且下游錯誤直接指向它。
2. **checkoutservice**：它是症狀端，呼叫 emailservice 失敗後延遲和錯誤都上升，而且我沒有看到它自己的資源異常。
3. **paymentservice**：這是湊數的第三名，沒有證據支持。它在訂單流程中，但 trace 中位數是 178 到 183，沒有異常。

## 不確定之處

- 我沒有逐分鐘確認 emailservice 的指標是從哪一秒開始惡化。我只確認 checkoutservice 的第一筆錯誤在 09:26:39，比回報的 09:28 早約 1 分多鐘。
- emailservice 本身的 log 裡沒有找到有意義的錯誤訊息，所以惡化的內部原因（例如記憶體洩漏或 socket 洩漏）無法確定。
- 兩個 GKE 節點的磁碟讀取與 `memory-active-bytes` 也有大幅跳動，但基準值接近 0，z 值失真。我不確定它們跟 emailservice 在不在同一個節點，所以不把它們算進證據。
- 第 3 名候選缺乏證據，排名不可靠。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "paymentservice"], "evidence": ["emailservice istio-latency-90 base 0.0047 -> after 0.253 (z=624); latency-99 0.0118 -> 1.679", "emailservice memory-working-set 4.35e7 -> 9.63e7, sockets 3.02 -> 6.88", "checkoutservice log (first at t+746s, ~09:26:39): failed to send order confirmation ... code = Unavailable desc = no healthy upstream (10 warnings)", "checkoutservice istio-latency-95 0.242 -> 1.001, trace errors 1 -> 9; p50 unchanged", "currencyservice/productcatalogservice/frontend/recommendationservice trace median and p95 unchanged before vs after"], "uncertain": ["no per-minute onset analysis of emailservice metrics; only checkoutservice's first error at 09:26:39 is confirmed", "emailservice's own logs show no meaningful error, so the internal cause (memory/socket leak?) is unknown", "node-level disk-read and memory-active spikes have ~0 baselines and unknown node placement, so not used as evidence", "third-ranked paymentservice has no supporting evidence"]}
```