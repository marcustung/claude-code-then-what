## 結論

**最可能的根因是 emailservice。** 它最先停止服務，checkoutservice 的錯誤全都出在寄確認信這一步。

### 證據

1. **emailservice 的 trace 在事發前就停了。**
   - trace 最後一筆在 1732371730（14:22:10 UTC），之後 emailservice 的 span 是 0 筆。事發前有 121 筆。
   - 約 11 秒後，checkoutservice 在 1732371741（14:22:21）出現第一筆寄信失敗 log。
   - 這比回報的 14:23 早約 1 分鐘。

2. **emailservice 的 metrics 劇烈變化。**
   - `emailservice_container-sockets` 的事發前平均是 3，事後是 1.08。
   - `memory-rss` 從 4.1e7 降到 1.66e7。
   - `network-receive-bytes` 與 `cpu-usage` 事後都是 0。
   - 這些指標的 z-score 都落在 -4 到 -64。
   - 整份 metrics 中，只有 emailservice 的變化這麼大。
   - 1732372018 時，`memory-rss` 從 45,281,280 掉到 4,460,544，疑似容器重啟。

3. **emailservice 的 log 顯示它反覆崩潰重啟。**
   - 重複出現 `AttributeError: '_Server' object has no attribute 'Check'`，共 8 筆，時間在 14:25、14:28、14:33 等。
   - 每次都伴隨 `starting the email service in dummy mode.`。
   - 事發前的正常 log 是 `A request to send order confirmation email to ... has been received.`。

4. **checkoutservice 的失敗是被動受害。**
   - `failed to send order confirmation ...: rpc error: code = Unavailable desc = no healthy ...` 或 `upstream conne...` 共 126 筆，時間範圍 14:22–14:33。
   - checkoutservice 的 trace 錯誤數從事發前 9 筆增加到事發後 117 筆。
   - checkoutservice 本身的 CPU 與記憶體沒有明顯變化（記憶體約 1.153e7 → 1.16e7）。

5. **frontend 與 productcatalogservice 等沒有明顯異常。**
   - trace 的 median 延遲前後幾乎一樣，例如 frontend 是 2198 → 2168。
   - 這些服務的錯誤數都是 0。

### 前 3 名候選
1. **emailservice**：證據如上。
2. **checkoutservice**：症狀最多（126 筆失敗 log、117 筆 trace 錯誤），但錯誤都來自呼叫 emailservice。
3. **paymentservice**：`memory-max-usage-bytes` 的 z 值是 8.8，`network-receive-bytes` 從 262 升到 536。這可能只是 checkout 重試造成的流量變化，不一定是異常。

### 不確定之處
- **崩潰原因未確認。** `'_Server' object has no attribute 'Check'` 看起來是 gRPC health check 的實作問題，可能是部署或程式 bug。我沒有看到部署紀錄，無法確認。
- **統計方法較粗。** 我用事發前後的平均值算 z-score，並以 14:23 為切點，沒有做更細的變化點偵測。
- **paymentservice 的變化沒有查證。** 我沒有驗證它是不是重試造成的。
- **我沒有確認 emailservice 的重啟次數。** 我只看到 log 中 14:25、14:28、14:33 的 3 次重啟訊息和一次記憶體驟降。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "paymentservice"], "evidence": ["emailservice 最後一筆 trace 在 1732371730（14:22:10），之後 0 筆（事發前 121 筆）", "checkoutservice 第一筆寄信失敗 log 在 1732371741，126 筆 'rpc error: code = Unavailable'", "emailservice log 出現 8 筆 AttributeError: '_Server' object has no attribute 'Check'，並反覆 'starting the email service in dummy mode'", "emailservice sockets 3→1.08、memory-rss 4.1e7→1.66e7、network 與 cpu 事後為 0，z-score -4 到 -64；1732372018 memory-rss 45281280→4460544（疑似重啟）", "checkoutservice trace 錯誤數 9→117，但其 CPU 與記憶體無明顯變化"], "uncertain": ["崩潰的直接原因（health check 實作或部署問題）未確認，沒有部署紀錄", "paymentservice 的 memory-max z=8.8、network-receive 262→536 是否為重試造成未驗證", "只用事發前後平均值做 z-score，以 14:23 為切點，沒有做變化點偵測", "emailservice 的重啟次數只確認 3 次 log 與 1 次記憶體驟降"]}
```