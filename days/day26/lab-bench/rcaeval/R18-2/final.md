**結論:根因服務最可能是 `carts`。** 信心中等。時序和基準比較都支持它,但資料裡沒有直接的因果證據。

## 證據

**1. `carts` 是最早偏離基準的服務。** 我拿事發前(< 02:55:00)的平均與標準差當基準,再看事發後的變化:
- `carts_container-cpu-usage-seconds-total` 的平均每步增量,從事發前 6.79 升到事發後 48.32。事發後 CPU 長期貼在約 49.9,而 `spec-cpu-quota` 是 50000。這看起來是 CPU 被打滿並受到節流,不過我沒有直接驗證節流。
- `carts_container-memory-cache` 從 45,056 跳到 2,260,992(約 50 倍),`memory-mapped-file` 同步跳升。兩者的偏離都早於 02:56:00 約 14 秒。
- `carts_container-cpu-system-seconds-total` 的增量,從 0.50 升到 34.67。
- `carts` 的記憶體 working-set 只從約 186 MB 升到約 197 MB,所以不像 OOM 型的問題,比較像 CPU 型的問題。

**2. 下游或上游服務在 `carts` 之後才出現延遲。**
- `carts_istio-latency-50` 從 0.159 升到 0.320(約 2 倍)。
- `orders_istio-latency-50` 從 0.060 升到 0.180(約 3 倍),在 T0 附近開始。`orders` 在這份資料裡有看到 `carts` 的依賴,但我沒有逐條 log 確認呼叫鏈。
- `front-end_istio-latency-90` 從 0.342 升到 0.596。
- `carts_istio-error-total` 一直是 0,所以症狀是變慢,不是失敗。使用者回報的「失敗」在 istio 錯誤指標上看不到。

**3. 其他異常出現得較晚,比較像是結果或獨立的雜訊。**
- `payment_container-memory-failures-total` 事發前是 0,第一次偏離約在 T0+252 秒,事發後平均 0.0435。它的 working-set 只有約 4.7 MB,且沒有變化。
- `queue-master_container-memory-failures-total` 從 0.32 升到 3.6,第一次偏離在 T0+683 秒。
- 節點 `nw9c` 與 `3px7` 的 disk-read-bytes 在 T0 後才出現讀取,首次偏離約在 T0+193 秒與 +282 秒,晚於 `carts`。我沒有查是哪個容器造成的。

## 不確定之處
- T0 我取 02:56:00 UTC(epoch 1705632960)。任務寫 02:56,但沒給秒數。`carts` 的偏離落在 T0 前 14 秒,可能只是 T0 取值的誤差。
- `carts` 的 log 沒有看到明確的錯誤。`UnknownHostException(zipkin)` 的 WARN 在事發前(02:43:57)就有,所以是背景雜訊,不是根因。
- `carts-db` 的 log 裡一直有 `Slow query`(`data.cart` 的 find)。事發前 02:43 就有,我沒有量化事發前後的差異,所以無法判斷 `carts-db` 是否為上游原因。
- `carts` 的 CPU 為什麼突然升高,我看不出來。可能是程式或流量變化,資料裡沒有部署或流量來源的資訊。
- 我沒有檢查 `front-end` 的 log(45,633 行)內容,所以沒確認使用者看到的失敗是哪類請求。

## 前三名候選
1. **`carts`**:最早偏離,CPU 貼到 quota,延遲上升。
2. **`orders`**:延遲約 3 倍,應該是 `carts` 的下游。我把它排在第二是因為它在 T0 附近的延遲變化最大,但它自身的 CPU 與記憶體沒有明顯異常。
3. **`carts-db`**:有 `Slow query`,是 `carts` 的資料來源。我把它排第三是因為無法排除它是上游原因,不是因為有直接證據。

```json
{"root_cause_service": "carts", "top3": ["carts", "orders", "carts-db"], "evidence": ["carts cpu-usage 每步增量 6.79 -> 48.32,貼近 spec-cpu-quota 50000", "carts memory-cache 45,056 -> 2,260,992,偏離早於 T0 約 14 秒", "carts cpu-system 增量 0.50 -> 34.67", "carts_istio-latency-50 0.159 -> 0.320;orders_istio-latency-50 0.060 -> 0.180;front-end latency-90 0.342 -> 0.596", "payment memory-failures 約 T0+252 秒、queue-master 約 T0+683 秒才偏離,晚於 carts", "carts_istio-error-total 全程為 0"], "uncertain": ["T0 取 02:56:00,carts 偏離早 14 秒可能是取值誤差", "carts log 無明確錯誤,zipkin WARN 事發前就有", "carts-db Slow query 事發前就有,未量化前後差異,無法排除為上游原因", "carts CPU 升高的原因看不出來", "未檢查 front-end log,未確認使用者看到的失敗請求類型", "nw9c、3px7 節點的 disk-read 來源容器未查"]}
```