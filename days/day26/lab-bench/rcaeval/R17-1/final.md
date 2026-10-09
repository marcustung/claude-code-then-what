## 結論

**最可能根因：catalogue。** 信心偏低到中等，因為這份資料裡的異常訊號很弱。

### 證據

1. **catalogue 是最早出現變化的服務。**
   - 約 23:04:52（事發前 3 分鐘）`catalogue_container-memory-cache` 從 49,152 B 跳到 343,953,408 B。後續穩定在約 6.1e8，事發前 12 分鐘一直是 4.92e4。
   - 同一秒 `catalogue_container-sockets` 從 5 變成 8，`memory-mapped-file` 從 0 變成 2,207,744。
   - `memory-working-set` 從約 6.3e6 變成約 2.0e7，之後在 1.2e7～2.75e7 間波動。
   - 前後均值：`memory-usage-bytes` 8.8e7 → 6.0e8，這是所有指標中最大的結構性變化之一。
2. **catalogue 的延遲在事發前後變差。**
   - `catalogue_istio-latency-95` 事發前均值 4.9ms，事發後 5.7ms。這是 z 分數最高的指標（8.1）。
   - 它偏離基準的時間點（`first`）約在 23:08:25，也就是事發後 25 秒。
   - 取樣到的 p99 在第 18 分鐘（約 23:10:37）出現 20.3ms，基準約 8ms。
   - 但 p50、p90 幾乎沒變（3.05→3.12ms、4.69→4.83ms），所以只是尾端延遲上升。
3. **catalogue 的 log 看不出明顯問題。**
   - 平均 `took` 事發前約 1.65～1.75ms，23:09～23:11 升到 1.80～1.86ms，之後回到約 1.7ms。
   - 沒有 `err=` 非 null 的紀錄。

### 排除項目與雜訊

- **front-end 沒有錯誤。** 每分鐘的 HTTP 狀態碼只有 200、201、202，事發前後分布一樣（約 240/122/60 次）。log 看不到使用者回報的失敗。
- **queue-master** 有大量 `RetryExec ... I/O exception`，約每分鐘 270 筆。這在事發前就存在，事發前 2322+513 筆、事發後 1281+297 筆，比例沒變，是基準雜訊，不是這次事件的原因。
- **user** 在 22:56～22:57 有 265 筆關鍵字命中，是事發前就有的現象，與事發時間不符。
- **user-db、carts-db、orders-db** 的記憶體只是緩慢線性成長，從頭到尾沒有拐點（例如 `orders-db memory-cache` 1.86e6 → 3.29e6），像是正常累積。
- **payment** 的 sockets 從 4 變成 5（約 23:15 起），變化太小，只能算弱訊號。

### 前 3 名

1. **catalogue**：最早的結構性變化加上延遲上升。
2. **carts**：`carts_istio-latency-95` 從 26.9ms 變成 34.5ms（z=1.6），但無明確起始點，也沒有錯誤。
3. **payment**：sockets 微增、`istio-latency-99` 在事發前有微小偏離。證據很弱。

### 不確定之處

- catalogue 的記憶體跳變比事發時間早約 3 分鐘，可能是前兆（例如記憶體或連線問題）。也可能只是 page cache 增長，是良性的。我無法從資料區分這兩者。
- 整份資料幾乎沒有錯誤 log，且 front-end 狀態碼沒有變化。使用者回報的「失敗」在資料中沒有直接證據。
- 我只用統計比較（事發前後均值、z 分數），沒有做因果檢定。事發時間按 23:08:00 UTC 估算。
- metrics 中沒有 catalogue-db 的有效異常，我沒有深入檢查它。

```json
{"root_cause_service": "catalogue", "top3": ["catalogue", "carts", "payment"], "evidence": ["catalogue_container-memory-cache 49,152B -> 343,953,408B at 23:04:52（事發前約3分鐘），穩定在約6.1e8", "catalogue sockets 5->8、memory-mapped-file 0->2,207,744 與記憶體同一秒跳變", "catalogue memory-working-set 約6.3e6 -> 約2.0e7", "catalogue_istio-latency-95 均值 4.9ms -> 5.7ms（z=8.1，事發後約25秒偏離），p99 在約23:10:37 出現 20.3ms（基準約8ms）", "front-end 事發前後狀態碼皆為 200/201/202，無錯誤；queue-master RetryExec 例外事發前就存在，比例不變"], "uncertain": ["記憶體跳變早事發約3分鐘，無法確定是前兆或良性 cache 增長", "資料中沒有失敗請求或錯誤 log，無法直接對應使用者回報的失敗", "catalogue 的延遲變化幅度小（p50/p90 幾乎不變），信心偏低", "carts 與 payment 的訊號很弱，排名依據不足", "事發時間按 23:08:00 UTC 估算，僅做統計比較，未做因果檢定"]}
```