**根因服務：orders**，把握度中高。最可能的原因是 orders 在 09:09 前後重啟或重新部署後，換上了有 bug 的版本。這個判斷有一個缺口：我沒有看到重啟的觸發原因。

## 證據

- **traces.csv 只有表頭、沒有資料**，所以呼叫鏈分析做不了。以下結論只靠 logs 和 metrics。
- **orders 在 09:09 開始異常。**
  - 09:09:09 出現 `MongoSocketOpenException ... orders-db:27017`。
  - 09:09:41 到 09:10:31 出現 3 次 `Starting`，09:10:31 才出現 `Started`，啟動花了約 1 分鐘。
  - 這段期間 orders 的 CPU 增量約 46 秒/分，事前約 1 秒/分。
  - 工作記憶體從約 3.4MB 升到約 6.5MB，09:12 之後又回到約 3.2MB。
- **重啟後的錯誤是 orders 自己的程式問題，不是 DB 問題。**
  - orders 在 09:10:34 到結束之間，一共 2576 行含 `Conflicting setter definitions for property "items"` 的 log（`CustomerOrder#setItems` 重複定義）。
  - 這是 `HttpMessageNotReadableException`，是 JSON 反序列化失敗。
  - front-end 在 09:09 之後的 `Order response` 狀態碼是 400 共 644 筆、503 共 93 筆、201 只有 4 筆。
  - 09:09 之前是 201 共 668 筆、406 共 74 筆，406 是 `Payment declined: amount exceeds 100.00`，屬於正常的業務拒絕。
  - 503 的內容是 `upstream connect error ... remote connection failure`，對應 orders 重啟期間無法連線。
- **front-end 的錯誤是被 orders 帶出來的。** front-end 每分鐘的錯誤行數從約 6 到 20 行，在 09:09 起跳到 112、128、130…，錯誤內容全是 orders 回的 400 和 503。
- **其他服務看起來沒有問題。**
  - payment 的 log 在 09:08 仍是 `Authorise result=true took=863ns`。
  - carts 在 09:09 之後沒有 error、exception 或 fail 的 log。
  - catalogue 和 user 沒有錯誤特徵。
  - 指標的事前/事後 z-score 排名靠前的多是量級極小的變化（如 `payment memory-max-usage` 7.545MB→7.628MB），不像真正的故障訊號，我不採用。

## 前 3 名候選

1. **orders**：最先出現異常，之後持續出現 400 的錯誤。
2. **orders-db**：09:09:09 的 Mongo 連線失敗指向它，`orders-db_container-sockets` 從 8 降到 5（約 09:06:18），再降到 2 或 3（約 09:09:18）。它自己的 log 只有每分鐘一次的 WiredTiger checkpoint，看不到錯誤，所以更像是 orders 重啟造成連線減少。
3. **front-end**：錯誤量最大，但內容都是轉述 orders 的回應，屬於下游症狀。

## 不確定之處

- orders 重啟的原因不明（可能是部署，也可能是 crash 或 OOM），log 裡沒有直接證據。
- orders-db 的 socket 在 09:06:18 先掉了一次，比 orders 的異常早約 3 分鐘。這可能是 orders-db 先出問題，我無法排除。
- `Conflicting setter` 的 400 持續到資料結束（09:20），表示問題沒有自行恢復。
- 沒有 trace，無法確認各服務之間的呼叫延遲。

```json
{"root_cause_service": "orders", "top3": ["orders", "orders-db", "front-end"], "evidence": ["orders log 09:09:09 MongoSocketOpenException 連 orders-db:27017，09:09:41 Starting、09:10:31 Started（重啟）", "orders 重啟後 2576 行 log 含 'Conflicting setter definitions for property \"items\"'（CustomerOrder#setItems）", "front-end 事發後 Order response：400 共 644、503 共 93、201 僅 4；事前為 201 共 668、406 共 74", "orders CPU 增量重啟期間約 46 秒/分，事前約 1 秒/分", "orders-db_container-sockets 8→5（約 09:06:18）→2~3（約 09:09:18）", "payment 與 carts 在 09:09 之後無錯誤 log"], "uncertain": ["traces.csv 無資料，無法驗證呼叫鏈", "orders 重啟的觸發原因不明（部署、crash 或 OOM）", "orders-db socket 在 09:06 先降，無法排除 orders-db 先出問題", "指標的事前/事後 z-score 多為微小變化，參考價值低"]}
```