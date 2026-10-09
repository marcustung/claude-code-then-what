## 結論

最可能的根因是 **emailservice**。它從約 15:25:05 UTC 起進入 crash loop,checkoutservice 因此在寄確認信時失敗。

### 證據

1. **emailservice 反覆崩潰(最早的異常)**
   - `logs.csv` 中 emailservice 的 pod `emailservice-775dbbdcb4-t9bmb` 重複出現:`starting the email service in dummy mode.` → `Traceback ... email_server.py line 199, in <module>` → `Exception: non-dummy mode not implemented yet`。
   - 第一次是 timestamp 1732289105(約 15:25:05 UTC),比使用者回報的 15:26 早約 1 分鐘。
   - 之後重啟間隔逐漸拉長:1732289112、129、164、221、319、493、801(對應 backoff)。
   - 啟動訊息與 Exception 各 8 次。
   - emailservice 的 log 量從事發前 164 筆降到事發後 20 筆,服務已不再正常處理請求。

2. **下游錯誤集中在 checkoutservice → emailservice**
   - `traces.csv` 中 statusCode=14 共 136 筆,**全部**是 `checkoutservice / SendOrderConfirmation`。最早的是 startTimeMillis 1732289104680,與 emailservice 第一次崩潰同時。
   - checkoutservice log 在事發後有 127 筆錯誤,事發前只有 9 筆。
   - 範例:`failed to send order confirmation to "brittanyparker@example.net": rpc error: code = Unavailable desc = no healthy upstream`。
   - 另有 `frontend PlaceOrder` 與 `checkoutservice PlaceOrder` 各 1 筆 statusCode=13,這應是錯誤向上傳遞的結果。

3. **其他服務看起來正常**
   - 多數服務的 trace 平均延遲事發前後約 1.0x,沒有明顯變慢。例如 `frontend GetProduct` 2426→2419 µs,`frontend GetCart` 4016→4041 µs。
   - 我用 z-score 比對 metrics 事發前後,沒有找到任何服務有顯著的 CPU、記憶體或網路異常。差異最大的 `shippingservice memory-rss` 只是 6.894e6→6.867e6,變化不到 1%,我視為雜訊。

### 前 3 名
1. **emailservice**:crash loop,是最早且唯一明確的故障源頭。
2. **checkoutservice**:錯誤集中在它的 `SendOrderConfirmation`(136 筆),是症狀的承受者與傳播者,不是源頭。
3. **frontend**:只有 1 筆 `PlaceOrder` 錯誤,屬於被連帶影響的最上層。

### 不確定之處
- 我沒有找到「為什麼」emailservice 會報 `non-dummy mode not implemented yet`。可能是部署或設定變更,例如環境變數或 image 版本,但資料裡沒有變更紀錄,這只是推測。
- 第 3 名的 frontend 是排除法的結果。除 checkoutservice 外,我沒看到其他服務有獨立異常,所以它其實缺乏直接證據。
- 使用者說「操作變慢」,但 trace 延遲沒有明顯上升。實際受影響的看起來是下單流程失敗(`PlaceOrder`),不是整體變慢。
- metrics 的許多累計型欄位更新稀疏,我的統計力道有限,所以主要結論依靠 logs 和 traces。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "frontend"], "evidence": ["emailservice pod emailservice-775dbbdcb4-t9bmb 從 timestamp 1732289105(約15:25:05 UTC)起反覆 'Exception: non-dummy mode not implemented yet',共 8 次,重啟間隔逐漸拉長", "traces 中 statusCode=14 共 136 筆,全部是 checkoutservice/SendOrderConfirmation,最早 1732289104680,與 emailservice 首次崩潰同時", "checkoutservice log 事發後 127 筆錯誤(事發前 9 筆),如 'failed to send order confirmation ... code = Unavailable desc = no healthy upstream'", "emailservice log 量由事發前 164 筆降至事發後 20 筆", "多數服務 trace 平均延遲事發前後約 1.0x,metrics 無顯著 CPU、記憶體異常"], "uncertain": ["未找到 emailservice 為何報 'non-dummy mode not implemented yet'(疑似設定或部署變更,僅為推測)", "frontend 列第3名主要依排除法,缺直接證據", "使用者回報的『變慢』在 trace 延遲中不明顯,實際影響看起來是下單流程失敗", "metrics 累計型欄位更新稀疏,統計判斷力有限"]}
```