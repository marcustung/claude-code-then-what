**根因：front-end（約 20:17:48 起有新版 pod 上線，之後 `POST /cart` 全部回 500）。這個結論有一部分是推論，見下方「不確定」。**

## 證據

**1. 症狀從 20:18 開始，只出現在 `POST /cart`（logs.csv）**
- `POST /cart` 在 20:18 前是 762 筆 201、0 筆 500。
- 20:18 起是 712 筆 500、只剩 5 筆 201。
- 其他路徑都沒變：`/orders` 201 有 669 筆（前）對 652 筆（後），`/register`、`/cards`、`/addresses`、`/catalogue` 也都維持 200。
- front-end 的錯誤類 log 每分鐘約 12–36 筆（20:17 前），20:18 起升到 61–96 筆。
- `front-end_istio-error-total` 的平均值從 0.24 升到 2.25。

**2. front-end 在 20:18 前後換了 pod（logs.csv 的 pod_name）**
- 舊 pod `front-end-f77549869-mpnfq` 的 log 範圍是 20:05:42 到 20:18:05，這段 `POST /cart` 有 767 筆 201。
- 新 pod `front-end-5f6d88487b-fvx7x` 最早的 log 是 1732393068（約 20:17:48），它的 `POST /cart` 全是 500（共 712 筆）。
- 另一個舊 pod `front-end-f77549869-nwglb` 只在 20:18:09–10 出現，log 有 `npm ERR! signal SIGTERM`，像是被終止。
- 三個 pod 的 ReplicaSet 雜湊不同（`f77549869` 對 `5f6d88487b`），看起來是一次新版本上線或滾動更新。
- front-end 的記憶體也在同一時間變動：working-set 在 20:18 附近約 5.4e7，之後短暫升到約 1.2e8，再回到約 5e7。

**3. 下游服務沒有出問題**
- `POST to carts` 在 front-end 的紀錄是 762 筆（前）和 717 筆（後）。
- carts 的 `Adding for user` 也剛好是 762 筆和 717 筆，所以請求都有送到 carts 並被處理。
- `carts_istio-error-total` 全程是 0。carts 的 latency-50 從 0.0155 到 0.0168，memory 約 3.42e8 不變，CPU 和 sockets 也沒有異常。
- carts-db 的 memory 約 9.0e7 到 9.5e7，fs 讀寫沒有明顯變化。
- catalogue、user、payment、orders 的 log 在事發前後格式與耗時都相近，例如 payment `Authorise result=true took≈1µs`。

**4. 排除的雜訊**
- queue-master 每分鐘約 200–260 筆 `AFUNIXSocketException ... unix://localhost:80` 和 `DockerSpawner ERROR`，但從 20:05 就開始、事發前後不變，是基準雜訊。
- orders 的 `POST /orders 406`（PaymentDeclined）事發前 93 筆、事發後 71 筆，也是基準行為。

## 前 3 名
1. **front-end**：新 pod 的 `POST /cart` 100% 回 500，而 carts 都有收到請求且沒有錯誤。
2. **carts**：500 發生在 `POST /cart` 的路徑上。但 carts 的 istio 錯誤是 0，metrics 也沒變，嫌疑低。
3. **carts-db**：carts 的後端，只做間接排除。20:18 附近 cpu 約 3.1 到 4.4 之間，沒有穩定的持續偏移。

## 不確定
- **traces.csv 是空的**（只有表頭），所以看不到 front-end 和 carts 之間的實際呼叫與回應碼。500 是 front-end 自己產生，還是 carts 回應異常後被轉成 500，是用 log 筆數推論出來的。
- front-end 的 log 只寫 `POST /cart 500 64.490 ms - 70`，沒有錯誤內容。回應只有 70 bytes，看起來像錯誤訊息。
- metrics 的 z-score 排名被標準差為 0 的欄位污染，例如 `user_container-memory-rss`、`queue-master_istio-latency-*`、`front_container-network-*`，我沒有採用。
- 新 pod 的第一筆 log 比 20:18 早約 12 秒（20:17:48 對 20:18:00）。這個差距可能是 log 收集延遲或事件時間不精確，我沒有進一步驗證。

```json
{"root_cause_service": "front-end", "top3": ["front-end", "carts", "carts-db"], "evidence": ["POST /cart: 762 筆 201、0 筆 500（20:18 前）；20:18 起 712 筆 500、5 筆 201，其他路徑 /orders /register /cards /addresses /catalogue 維持 200", "front-end pod 由 front-end-f77549869-mpnfq 換成 front-end-5f6d88487b-fvx7x（約 20:17:48 起），新 pod 的 POST /cart 共 712 筆全是 500；舊 pod nwglb 在 20:18:09 出現 npm ERR! signal SIGTERM", "front-end 的 POST to carts 為 762 筆(前)/717 筆(後)，carts 的 Adding for user 也是 762/717，請求都送達並處理；carts_istio-error-total 全程 0，carts latency-50 為 0.0155 到 0.0168，memory 約 3.42e8 不變", "front-end_istio-error-total 平均從 0.24 升到 2.25；front-end 錯誤類 log 從約 12–36 筆/分鐘升到 61–96 筆/分鐘", "queue-master 的 AFUNIXSocketException/DockerSpawner ERROR 事發前後約 200–260 筆/分鐘不變，屬基準雜訊"], "uncertain": ["traces.csv 只有表頭，沒有呼叫鏈，無法確認 500 是 front-end 自己產生還是 carts 回應異常後轉成 500", "front-end 的 500 log 沒有錯誤內容，只知回應 70 bytes", "metrics 的 z-score 排名被標準差為 0 的欄位污染，未採用", "新 pod 的第一筆 log 比 20:18 早約 12 秒，可能是 log 收集延遲，未驗證", "根因是新版部署還是 front-end 與 carts 之間的相容性問題，資料不足以區分"]}
```