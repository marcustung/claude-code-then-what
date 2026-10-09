**結論：最可能的根因服務是 `carts`，`orders` 與 `front-end` 是受波及的下游。** 但 carts 與 orders 的起始時間只差 2 秒，順序判斷信心中等。

## 證據

**1. 異常起點在 04:58:45 左右，比回報的 05:01 早約 2 分鐘。** metrics 為每秒一筆，從 04:46:33 到 05:10:33，共 1441 筆。istio p90 延遲的第一次跳升如下：

| 服務 | 時間 (UTC) | 事發前 → 事發後 p90 |
|---|---|---|
| orders | 04:58:45 (`time=1705726725`) | 0.05s → 0.70s |
| carts | 04:58:47 (`time=1705726727`) | 0.044s → 0.955s |
| front-end | 04:59:00 | 0.086s → 0.748s，之後約 1.9s |

**2. carts 是受影響最重的服務。** 它的 p90 從約 0.045s 升到約 2.26s，約 50 倍，且之後持續到資料結束。

**3. 其他服務的延遲沒有變化。**
- payment 與 shipping 的 p90 都維持 0.005s。shipping 只在 `time=1705727099` 附近有一次短暫突波（0.041s），之後恢復。
- payment 的 log 全程是 `Authorise result=true took≈1µs`，沒有異常。

**4. 拓撲上 carts 在 orders 與 front-end 的上游。** 這是我依 Sock Shop 架構與 log 推斷，資料本身沒有直接標示呼叫關係。
- 症狀順序是 carts / orders 先升，front-end 隨後。
- front-end 的 sockets 從約 7 升到約 17–25，像是請求堆積。
- carts 的 sockets 從 20 升到 28。

**5. carts 的 CPU 與記憶體沒有明顯變化，carts-db 也正常。**
- carts CPU 在 04:58 前後都約 1.3–1.6。
- carts-db CPU 約 6–7，沒有升高，sockets 維持 15。
- 這顯示瓶頸不像是資源耗盡，也不像是 carts-db 變慢。

## Top 3

1. **carts**：延遲最嚴重（約 50 倍）、位於上游，且持續不恢復。
2. **orders**：p90 從 0.05s 升到 0.70s，起始只早 carts 2 秒。
3. **front-end**：p90 約 1.9s，sockets 約 7 → 17–25，較像受波及的下游。

## 不確定之處

- **起點順序無法確定。** metrics 看起來有 forward-fill，orders 比 carts 早 2 秒在取樣誤差內。orders 的 p50 沒變、p90 只有 0.7s，低於 carts 的 0.955s，與「orders 被 carts 拖慢」一致。
- **看不到 carts 內部的具體原因。** carts 的 log 沒有新增錯誤。`UnknownHostException: zipkin` 共 343 筆，從 04:48 起就持續出現，是事發前就有的雜訊，不是這次事件的原因。queue-master 的錯誤量也是事前事後都約每分鐘 220–280 筆，同樣是基準雜訊。
- **未排查 carts 與 orders 之間的網路問題**，也不能排除外部因素，例如 carts 的連線池或執行緒問題。這些資料裡看不到。
- **前期統計有一個錯誤。** 我最初用 05:01 當切點做 z-score 排名，結果被極小變異的欄位干擾，之後改用 04:58:45 附近的逐秒資料，上面的數字都來自後者。
- **沒有逐一檢查 user 與 catalogue 的延遲。** 它們沒出現在變化排名前列，但我沒有單獨確認。

```json
{"root_cause_service": "carts", "top3": ["carts", "orders", "front-end"], "evidence": ["carts istio p90 latency 0.044s -> 0.955s at 04:58:47 (time=1705726727), ~2.26s steady afterwards", "orders p90 0.05s -> 0.70s at 04:58:45, front-end p90 0.086s -> 0.75s at 04:59:00 then ~1.9s", "payment/shipping p90 stay at 0.005s; payment logs show Authorise took~1µs", "carts sockets 20->28, front-end sockets ~7->17-25; carts CPU and carts-db CPU/sockets unchanged", "carts zipkin UnknownHostException (343 lines) starts 04:48, pre-incident noise"], "uncertain": ["orders vs carts onset differs by only 2s, within sampling resolution (metrics look forward-filled)", "no log or resource anomaly shows why carts slowed down", "downstream call direction orders->carts is inferred from Sock Shop architecture, not from the data", "user and catalogue latency not individually checked", "network or connection-pool issues between carts and orders not ruled out"]}
```