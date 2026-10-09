**根因服務:recommendationservice**(信心中高。事發後指標與 trace 的異常都集中在它身上,但 log 沒有直接證據。)

## 證據

**1. 異常指標幾乎都屬於 recommendationservice。**
我取事發前(< 23:51)與事發後(≥ 23:52)的均值,以事發前標準差標準化後排序。前 10 名中 9 個是它的指標:

| 指標 | 事發前均值 | 事發後均值 |
|---|---|---|
| `container-memory-usage-bytes` | 47.2 MB | 442 MB |
| `container-memory-cache` | 245,760 | 3.83 億 |
| `container-fs-reads-bytes-total` | 0 | 4,664 萬 |
| `container-fs-writes-bytes-total` | 0 | 4,664 萬 |
| `container-blkio-device-usage-total` | 0 | 9.3e9 |
| `istio-latency-95` | 0.010 s | 0.227 s |
| `istio-latency-50` | 0.007 s | 0.048 s |
| `container-cpu-system-seconds-total` | 0.35 | 11.97 |

- 其餘一個是節點 `0e4z` 的磁碟寫入(見「不確定之處」)。
- `container-memory-rss` 只從 45.8 MB 增到 47.4 MB,`working-set` 只從 46.9 MB 增到 61.4 MB。
- 增加的主要是 page cache 與磁碟 I/O,不是應用程式堆積記憶體。

**2. 時間點最早,且是階躍式變化。**
- `memory-usage-bytes` 在 t+720 s 時仍是 47.2 MB,到 t+780 s 變成 471.8 MB(約 10 倍)。
- 以 1.5 倍閾值判定,起點是 epoch 1705535479(約 23:51:19),比回報的 23:52 早約 40 秒。
- 之後它維持在約 471 MB,中間幾次掉到 179 MB、333 MB、166 MB。

**3. 下游先正常、上游後變慢。**
- recommendationservice 的 `istio-latency-95` 從 0.010 s 跳到 0.23 s,每個取樣點都一樣,屬於持續性的階躍。
- `frontend_istio-latency-50` 從約 0.048 s 升到約 0.097 s,約為 2 倍。
- `frontend_istio-latency-95` 從約 0.22 s 升到 0.25–0.36 s,幅度較小。
- `productcatalogservice_istio-latency-95` 全程維持 0.005 s,沒有變化。

**4. Trace 中它的長尾明顯惡化。**
以 23:52 前後各一段的 span duration(單位 µs,資料單位未另外確認)比較:

| 服務 | 事發前 / 事發後 p50 | 事發前 / 事發後 p95 |
|---|---|---|
| recommendationservice | 3376 / 4481 | 5486 / **99369**(約 18 倍) |
| frontendservice | 3680 / 3801 | 63442 / 116221(約 1.8 倍) |
| checkoutservice | 4013 / 4040 | 71823 / 65329(無惡化) |
| productcatalogservice、currencyservice、paymentservice、emailservice | 無變化 | 無變化 |

- `statusCode` 欄位沒有非 0 的值,所以沒有明確的失敗 span。「失敗」的症狀在這份資料裡看不到。

## 前 3 名候選
1. **recommendationservice**:指標、時間點、trace 長尾三項都指向它。
2. **frontend**:延遲變慢,但屬於下游拖累的結果,它自己的 CPU 與記憶體沒有類似的階躍。
3. **節點 `gke-...-0e4z`**:磁碟寫入量從 2.66 MB 增到 51.9 MB(約 108 σ),可能是同節點的 recommendationservice 造成的。

## 不確定之處
- logs.csv 沒有任何 error/warn 級別的 log(只有 info、debug、INFO 和空值),也沒有 `error` 欄位的內容。我沒有逐條檢視 recommendationservice 的 log 內容,所以沒有 log 能直接解釋它為何變慢。
- 記憶體與磁碟 I/O 暴增的原因我只能推測:可能是檔案讀寫、快取行為或記憶體限制。資料裡看不出是哪一種。
- 節點磁碟異常是 recommendationservice 的結果還是原因,我無法分辨。我也沒有確認 recommendationservice 與節點 `0e4z` 在同一台機器上。
- 異常起點(約 23:51:19)比回報的 23:52 早,我認為差距在合理範圍內,但沒有更細的資料可驗證。

```json
{"root_cause_service": "recommendationservice", "top3": ["recommendationservice", "frontend", "gke-gke-cluster-default-pool-2e1807ce-0e4z (node)"], "evidence": ["recommendationservice memory-usage-bytes 47.2MB -> 471.8MB step at epoch ~1705535479 (23:51:19), earlier than reported 23:52", "recommendationservice istio-latency-95 0.010s -> 0.227s; latency-50 0.007s -> 0.048s", "recommendationservice memory-cache 245,760 -> 3.83e8; fs read/write bytes 0 -> 4.66e7; blkio 0 -> 9.3e9; cpu-system 0.35 -> 11.97", "memory-rss only 45.8MB -> 47.4MB, so growth is mostly page cache / disk I/O", "trace p95 of recommendationservice 5486 -> 99369; frontend p95 63442 -> 116221; other services unchanged", "frontend istio-latency-50 0.048s -> 0.097s, a downstream symptom", "productcatalogservice istio-latency-95 constant at 0.005s"], "uncertain": ["logs.csv has no error/warn level entries and an empty error column; no log directly explains the cause", "cause of the memory and disk I/O surge is unknown (file I/O, caching or memory limit)", "whether node 0e4z disk write growth (2.66MB -> 51.9MB) is cause or effect, and whether recommendationservice runs on that node, is unconfirmed", "no trace statusCode failures, so the failure symptom is not visible in this data"]}
```