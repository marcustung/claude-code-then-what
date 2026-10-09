## 結論

**最可能的根因是 emailservice。** 它的異常出現得最早，也最明顯，而且是下游 checkoutservice 變慢的原因。

### 證據

1. **指標比較**（以 05:32 為界，事發前當基準，異常程度以標準差倍數計）
   - 除了一個節點層級的 `node-memory-active-bytes`（9,066 → 2.29e6），emailservice 的指標最突出。我認為那個節點指標是系統層的雜訊，不是服務問題。
   - `emailservice_istio-latency-50`：0.00305 → 0.0102 秒（35σ）。
   - `emailservice_container-cpu-usage-seconds-total`：0.48 → 7.74（5.7σ）。
   - `emailservice_container-sockets`：3.2 → 9.2。
   - `emailservice_container-memory-working-set-bytes`：43.7MB → 53.5MB。
   - istio P90 延遲：0.0066 → 0.0405 秒。P99 延遲：0.0100 → 0.0490 秒。

2. **起始時間**
   - istio latency-50 在 1705728664（05:31:04）從 0.0049 跳到 0.0518，到 05:32:00 左右達 0.0638。事發前約為 0.003。
   - 這個時間比使用者回報的 05:32 早約 1 分鐘。
   - 延遲在約 05:34 之後回落（05:35:00 是 0.0043），整個異常約 5 分鐘。

3. **Trace**（emailservice 每分鐘平均 duration，單位 µs）
   - 05:26 到 05:29 約為 150–200。
   - 05:30 為 3,418（最大 93,587）。05:31 為 5,105，05:33 為 5,995。
   - 05:36 起回到約 180。
   - 同一時段 checkoutservice 平均 duration 從約 13–14k 升到 05:31 的 24.8k，05:36 後回到約 14–15k。
   - checkoutservice 的 log 有 `order confirmation email sent`，表示它呼叫 emailservice，延遲可能因此傳遞過去。

4. **次要候選**
   - paymentservice 在 05:32 平均 duration 418，最大 3,667（基準約 200）。
   - paymentservice 的記憶體指標有輕微上升（4σ，34.2MB → 35.4MB）。
   - 這個幅度很小，只持續約 1 分鐘。
   - checkoutservice 的 istio-latency-99 為 0.31 → 0.45 秒（1.6σ）。
   - 這很可能是受 emailservice 影響的症狀，不是根因。

### 不確定之處
- **Log 沒有錯誤訊息。** logs.csv 沒有 error 或 warning 層級的紀錄（`error` 欄全空），所以沒有 log 證據支持根因，只能靠指標和 trace。
- **起始時間早於回報。** emailservice 在 05:30–05:31 就開始變慢，早於使用者回報的 05:32。我認為這是回報時間較晚，但沒有直接驗證。
- **Trace 沒有失敗紀錄。** 所有 span 的 statusCode 都是 0，沒有失敗的 span。「操作失敗」在資料裡看不到。
- **缺少 cartservice 的 trace。** trace 裡沒有 cartservice 的 span，無法用 trace 排除它。cartservice 的 memory-cache 變化（2.055e7 → 2.059e7，約 0.2%）統計上顯著但幅度很小，我判斷是雜訊。
- **CPU 計數器不單調。** emailservice 的 cpu-usage 計數器有負的差值（例如 -3.177），看起來像計數器重置或取樣誤差。因此 CPU 的數值只能當趨勢參考。
- **沒有查出 emailservice 變慢的原因。** 我看不出是 CPU、記憶體還是 socket 數導致，也沒有看到外部觸發事件。
- **checkoutservice 的因果是推論。** checkoutservice 的延遲在時間上同步上升，但幅度不大（約 14k → 25k），我沒有逐 trace 驗證它是否真的在等 emailservice。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "paymentservice"], "evidence": ["emailservice istio-latency-50 0.00305 -> 0.0102 (35σ)；05:31:04 起從 0.0049 跳到 0.0518", "emailservice cpu-usage-seconds-total 0.48 -> 7.74, sockets 3.2 -> 9.2, working-set 43.7MB -> 53.5MB", "trace: emailservice 平均 duration 05:29 約 202µs -> 05:31 5,105µs（最大 97,968），05:36 後回到約 180", "checkoutservice 平均 duration 05:29 12.7k -> 05:31 24.8k，05:36 後回到約 15k；log 顯示 checkout 會呼叫 emailservice", "paymentservice 僅在 05:32 平均 418µs（基準約 200），幅度小且短暫"], "uncertain": ["logs.csv 沒有 error/warning 層級紀錄，沒有 log 證據", "emailservice 異常起點 05:31:04 早於回報的 05:32", "traces 的 statusCode 全為 0，看不到失敗的 span", "trace 沒有 cartservice 的 span，無法排除它", "emailservice cpu 計數器有負差值，數值可能不可靠", "未查出 emailservice 變慢的具體原因（CPU、記憶體或外部觸發）", "checkoutservice 延遲是否由 emailservice 造成僅為時間上的推論"]}
```