## 結論

根因最可能是 **orders**。它的 CPU 與記憶體先飽和，延遲與下游症狀隨後才出現。

### 證據（`data/metrics.csv`，1 秒取樣，07:05:05–07:29:05）

- **orders CPU 飽和**：事發前平均約 1.1–1.4，07:17:28 起升到約 37，07:18 之後穩定在約 77–78。CPU quota 為 80000，所以已經頂到上限。
- **orders 記憶體撞上限**：working set 基準約 332 MB，限制為 1073741824（1 GiB）。07:17:11 達 1073717248，之後在 369 MB 到 1.07 GB 之間大幅震盪。例如 07:22:40 為 1.07 GB，07:22:58 掉到 369 MB，07:23:11 又回到 1.07 GB。這很像記憶體壓力下容器被重啟或 GC 抖動，但我沒有直接看到重啟事件。
- **orders 延遲暴增**，並且先於前端：
  - orders latency-99 從 0.05 升到約 0.9，首次超過 0.5 是 07:17:25。
  - front-end latency-99 從 0.099 升到約 0.45–0.7，首次超過 0.3 是 07:17:45，晚了約 20 秒。
  - orders latency-90 從 0.054 升到 0.51，latency-95 從 0.064 升到 0.68。
- **orders 的 sockets 增加**：從 16–17 升到 22–27。
- **orders log**（07:20:37）：`WARN ... org.mongodb.driver.connection : Got socket exception on connection ...`、`ERROR ... dispatcherServlet ... threw exception`，原因是 `com.mongodb.MongoSocketReadException: Prematurely reached end of stream`。這顯示 orders 到 orders-db 的連線被中斷。orders 在整份 log 中只有 9 筆 error/exception 類訊息。

### 其他候選的比較

- **front-end**：latency-99 為 0.099 → 0.52，但比 orders 晚約 20 秒。它的 CPU 沒變（4.53 → 4.51），應是被下游拖慢的受害者。
- **carts**：latency-99 為 0.072 → 0.246，CPU 沒變（1.44 → 1.44）。基準期就有雜訊，例如 07:08:00 已有 0.158，所以這變化不一定是事故造成。carts-db 的 CPU 從 5.98 升到 7.44，可能與 orders 的流量有關，也可能只是自然波動。
- **shipping**：CPU 從 0.441 升到 0.739，延遲小幅上升（latency-90 為 0.0047 → 0.0051）。幅度很小，不像根因。
- **user-db**（sockets 8 → 11）與 **payment**（sockets 4 → 6）：sockets 在 07:21 之後才增加，晚於 orders，也沒有延遲或 CPU 的明顯變化。可能是連線重試的副作用，也可能無關。

### 不確定之處

1. orders CPU 在 07:08:38 起就有約 12 的台階。基準期前 500 秒的最大值也是 12.3，所以我視為基準的一部分，不算事故起點。如果它其實是早期徵兆，起點會提早到 07:08。
2. 事故起點與使用者回報的 07:19 不完全吻合。指標顯示 07:17:11–07:17:28 就已惡化，我猜是回報有延遲，但無法證實。
3. 沒有找到 orders 自己出問題的原因，例如記憶體洩漏或某個請求路徑耗盡資源。orders-db 的 CPU 沒變（0.411 → 0.414），所以資料庫不像上游。log 裡的 MongoSocketReadException 發生在 07:20，比 orders 飽和晚約 3 分鐘，因此較像結果，不是起因。
4. queue-master 有 5872 筆符合 error/warn 關鍵字的 log，但它從 07:05 起每分鐘約 232–264 筆，事發前後沒變化，我判斷是背景雜訊，沒有深入檢查。
5. 我沒有找到 orders 受到上游壓力（例如流量暴增）的證據，但也沒有逐一檢查 request-total。

```json
{"root_cause_service": "orders", "top3": ["orders", "front-end", "carts"], "evidence": ["orders CPU 約 1.1–1.4 → 37（07:17:28 起）→ 約 77（quota 80000，已飽和）", "orders 記憶體 working set 基準約 332MB，07:17:11 撞到 1GiB 上限，之後在 369MB–1.07GB 間震盪", "orders latency-99 為 0.05 → 約 0.9（07:17:25 首次超過 0.5），比 front-end latency-99（0.099 → 0.5，07:17:45）早約 20 秒", "orders log 07:20:37：com.mongodb.MongoSocketReadException: Prematurely reached end of stream", "front-end CPU 4.53 → 4.51、carts CPU 1.44 → 1.44 沒變，兩者較像受害者"], "uncertain": ["orders CPU 在 07:08:38 起有約 12 的台階，基準期前 500 秒最大值也是 12.3，視為基準，但可能是早期徵兆", "指標在 07:17 就惡化，與回報的 07:19 不完全吻合", "不知道 orders 自身飽和的觸發原因（記憶體洩漏、特定請求路徑或流量），MongoSocketReadException 晚於飽和約 3 分鐘，較像結果", "carts 的延遲上升在基準期就有雜訊，是否與事故相關不確定", "user-db 與 payment 的 sockets 增加與 shipping CPU 小幅上升，可能是副作用或無關", "queue-master 有大量 error/warn 關鍵字 log，但事發前後速率不變，判斷為背景雜訊，未深入檢查"]}
```