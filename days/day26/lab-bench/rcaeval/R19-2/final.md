## 結論

**最可能根因：`orders`。** 它是最先、也是偏離最大的服務，而且偏離發生在使用者回報時間（07:18）之前。

### 證據（基準為 07:18 前的資料）

- **orders CPU 在 07:17:41 左右暴衝。**
  - `orders_container-cpu-usage-seconds-total` 事前均值約 3.97，事後均值約 75.07。
  - 07:17:35 的取樣是 1.08，07:17:35 之後約 30 秒的取樣是 37.15，之後穩定在約 77–78。
  - system 與 user CPU 都升高：system 約 1.06→25.4，user 約 2.91→49.7。
  - 以 4σ 判定，最早偏離時間是 1705735061（約 07:17:41），早於回報時間約 20 秒。
- **orders 記憶體壓力。**
  - `memory-failures-total` 均值約 5,957→185,111。
  - `memory-usage-bytes` 事前穩定在約 332 MB，事後在 350 MB 到 1,073,741,824 bytes（1 GiB）之間劇烈波動，多次碰到 1 GiB，看起來像是撞到記憶體上限。
  - 我沒有讀取 limit 欄位，所以「上限是 1 GiB」是推測。
- **orders 延遲上升。**
  - `orders_istio-latency-95`：事前約 0.064 s，事後均值約 0.67 s，07:18 之後取樣約 0.7 s。
  - latency-99：事前約 0.09 s，事後約 0.93 s。
  - orders 延遲在 1705735050–60 就開始偏離。
- **下游症狀出現較晚，幅度也較小。**
  - `front-end_istio-latency-99`：事前 0.11 s，事後 0.51 s。
  - `carts_istio-latency-95`：事前 0.048 s，事後 0.098 s。
  - 兩者的偏離點都是 1705735062–69，晚於 orders。
- **orders log。**
  - 07:20:37 出現 `org.mongodb.driver.connection : Got socket exception on connection ... to orders-db:27017`，並有 `Closed connection` 與 `Servlet.service() ... in` 的錯誤。
  - 07:20 的 log 量是 250 行，平常約 120 行，約 2 倍。這是在 CPU 與延遲異常之後才出現，所以應是結果，不是起因。

### 前 3 名候選

1. **orders**：證據如上。
2. **front-end**：延遲上升，但出現在 orders 之後，且 log 錯誤在 07:21–07:24 才升高（37–41 條/分），像是被 orders 拖累。
3. **carts**：延遲有上升（latency-90 z≈13），但幅度小，且與 orders 同時或稍晚。

orders-db 的 CPU 沒有變化（約 0.43 前後都是），所以 orders-db 不太可能是源頭。

### 不確定之處

- 我沒有看到導致 orders CPU 暴衝的直接原因（例如 GC、無窮迴圈、請求量暴增或部署變更）。log 沒有 OOM 或 GC 字樣，我只搜尋過部分關鍵字。
- 記憶體上限值未驗證。
- `orders_istio-error-total` 與節點 disk-read 的 z 值是數十萬到上億，是因為事前標準差為 0，不代表真的大幅異常。事後 error 均值只有 0.003，我不把它當作證據。
- log 的 level 欄全空，無法用層級篩選，只能用關鍵字，因此錯誤數可能漏算。
- queue-master 的「錯誤」關鍵字命中很多（5,908 條），但從 07:05 起每分鐘都穩定在 230–270 條，疑似是常態輸出，我沒有深入確認。

```json
{"root_cause_service": "orders", "top3": ["orders", "front-end", "carts"], "evidence": ["orders cpu-usage-seconds-total 事前均值≈3.97 → 事後≈75.07，最早偏離 1705735061 (約07:17:41)，早於 07:18 回報", "orders memory-failures-total 事前≈5,957 → 事後≈185,111；memory-usage 多次達 1073741824 bytes", "orders istio-latency-95 事前≈0.064s → 事後≈0.67s；latency-99 ≈0.09→0.93s", "front-end latency-99 0.11→0.51s、carts latency-95 0.048→0.098s，偏離點 1705735062–69，晚於 orders", "orders log 07:20:37 出現 mongodb 'Got socket exception ... orders-db:27017'，07:20 log 量 250 行（平常約120），為後發症狀", "orders-db CPU 約 0.43 前後無變化"], "uncertain": ["未找到 orders CPU 暴衝的直接原因（GC、請求暴增、部署變更等）", "記憶體上限是否為 1GiB 未驗證（未讀 limit 欄位）", "log level 欄全空，錯誤計數靠關鍵字，可能有漏", "queue-master 關鍵字命中多但疑似常態輸出，未深入確認"]}
```