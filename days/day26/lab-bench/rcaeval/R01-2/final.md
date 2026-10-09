**根因服務：adservice。** 約 11:33:30 UTC 重啟後沒有恢復正常服務，frontend 呼叫它全部失敗。

## 證據

1. **adservice 在 11:33 重啟。**
   - 最後一筆 adservice log 時間戳是 1732275217（約 11:33:37）。
   - 最後幾行是 `AdService starting.`、`Tracing enabled - Stackdriver exporter initialized.`、`Ad Service started, listening on 9555`。
   - 之後再也沒有任何 adservice log。重啟前每分鐘約 175–185 筆，11:33 那分鐘只剩 97 筆。
   - `adservice_container-memory-working-set-bytes` 在 11:33→11:34 從約 89.7MB 跳到 161MB，11:39 又掉到 75.9MB。我解讀為重啟或 crash 的特徵。

2. **adservice 的網路指標在 11:34 起全部消失。**
   - receive/transmit packets 與 bytes 事發前約 7 packets/s、約 1.1 萬 bytes/s，11:34 之後是空值。
   - 這些指標事發前後的平均差距約 2.3–2.4 個標準差，是 `adservice_container-network-*` 以外少數明顯偏離基準的欄位之一。

3. **frontend 呼叫 adservice 全數失敗。**
   - traces 中 `hipstershop.AdService/GetAds` 的 `statusCode=12.0`（gRPC UNIMPLEMENTED）共 2109 筆，是所有 12.0 錯誤的 100%。第一筆在 11:33:38，緊接在重啟之後。
   - frontend log 的 `failed to retrieve ads` 從 11:33 的 86 筆起，11:34–11:44 每分鐘約 160–198 筆，一直持續。
   - traces.csv 裡 adservice 本身沒有任何 span，所以從 trace 端看不到它的服務端行為。

4. **其他服務看不到先出問題的跡象。**
   - 兩個 istio latency 欄位 z 分數看起來高，但差距很小：`shippingservice` p99 是 0.0049→0.0053，`recommendationservice` p99 是 0.0099→0.0108。
   - 其餘服務的 CPU、記憶體、延遲變化都在基準的 1–2 個標準差內。
   - 其他服務的 trace 平均耗時事發後沒有變慢，例如 productcatalogservice 平均 37→36 µs。

## Top 3

1. **adservice**：證據如上。
2. **frontend**：它是症狀承受方。`failed to retrieve ads` 之外，11:35 的 `frontend-external_istio-error-total` 有一次 0.067。它沒有自己先出問題的跡象，所以排第二只是因為它是使用者看到錯誤的地方。
3. **recommendationservice**：p99 延遲略增，但幅度很小，缺乏因果證據，可能只是雜訊。我只是需要補第三名，這個排名的把握很低。

## 不確定之處

- 無法從資料判定 adservice 為何重啟，例如 OOM 或 crash，因為沒有重啟前的錯誤 log，也沒有 `memory-failures-total` 的變化。
- 重啟後 `GetAds` 回 UNIMPLEMENTED 而非連線失敗，原因不明。也不確定這是否是故障注入的設計。
- adservice 的 `istio-request-total` 在事發後仍維持約 5–6/s，`istio-error-total` 一直是 0。這與「全部失敗」不一致，可能是 sidecar 計到了請求但沒計到錯誤，我沒有進一步驗證。
- 事件通報的 11:36 比我看到的 11:33:38 晚約 2–3 分鐘。我推測是使用者感知延遲，但沒有資料可證實。
- 我只比較了事發前後的平均值，沒有逐指標做變點偵測，小幅度的異常可能漏掉。

```json
{"root_cause_service": "adservice", "top3": ["adservice", "frontend", "recommendationservice"], "evidence": ["adservice 最後一筆 log 約 11:33:37，內容為 'AdService starting.' ... 'Ad Service started, listening on 9555'，之後無任何 adservice log", "adservice memory-working-set 11:33→11:34 由約 89.7MB 跳到 161MB，11:39 降至 75.9MB；network receive/transmit 指標自 11:34 起全為空值（事發前約 7 packets/s、約 1.1 萬 bytes/s）", "traces 中 hipstershop.AdService/GetAds statusCode=12.0 共 2109 筆，佔全部 12.0 錯誤的 100%，首筆 11:33:38", "frontend log 'failed to retrieve ads' 11:33 起 86 筆，11:34–11:44 每分鐘約 160–198 筆", "其他服務 CPU、記憶體、延遲變化皆在基準 1–2 個標準差內，trace 平均耗時事發後未變慢"], "uncertain": ["無法判定 adservice 重啟原因（OOM 或 crash），無重啟前錯誤 log", "重啟後回 UNIMPLEMENTED 而非連線失敗，原因不明，也不確定是否為故障注入設計", "adservice istio-request-total 事發後仍約 5–6/s 且 istio-error-total 為 0，與全部失敗不一致，未驗證", "事件通報 11:36 與實際首個錯誤 11:33:38 相差 2–3 分鐘，推測為使用者感知延遲，無資料證實", "第三名 recommendationservice 證據薄弱，僅 p99 延遲小幅上升", "只比較事發前後平均值，未逐指標做變點偵測，小幅異常可能漏掉"]}
```