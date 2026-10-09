## 結論

最可能的根因服務是 **carts**。這是依時間點與間接證據推斷的，沒有任何 log 直接寫出「503 來自 carts」。

### 證據

1. **carts 的 WARN/ERROR 在事發後暴增。**
   - 以事發點 12:44 前後各算（基準期約 800 秒、事發後約 641 秒），carts 的 warn/error 類 log 從 23 筆增為 668 筆。
   - 事發後每 2 分鐘約 120–135 筆，持續到約 +10 分鐘。
   - 典型內容：`WARN [carts,...] PageNotFound : Request method 'POST' not supported`。
   - `PageNotFound` 事發後每分鐘約 60 筆（第 0 分鐘 22、第 1–4 分鐘 59–67）。

2. **carts 的資源在事發當下跳升（事發後與事發前平均值比較）。**
   - `carts_container-memory-working-set-bytes`：約 330 MB 升到 580–674 MB（事發點約 +0 秒起），之後回到約 345 MB。
   - 整段事發後平均從 343 MB 升到 468 MB。
   - `carts_container-sockets`：事發前約 20，峰值 70，之後穩定在約 30（平均 20.5 → 36.2）。
   - `carts-db_container-sockets`：16 → 3 → 26，之後穩定在 26。這是明顯的連線重置。
   - 在我算的所有指標裡，carts 相關欄位的變化幅度名列前茅。

3. **下游錯誤與 carts 同時出現。**
   - orders 在 12:43:01 開始出現 `HttpServerErrorException: 503 Service Unavailable`，堆疊在 `AsyncGetService.getDataList`。
   - 每分鐘次數：-1 分鐘 64 次、0 分鐘 39 次，之後降到 1–2 次。
   - 同時 front-end 回報 `Order response: statusCode 500 ... IllegalStateException "Unable to creat..."`。這與使用者回報的「操作失敗」吻合。

### 不確定之處

- **503 的來源服務沒有被確認。** `getDataList` 是 orders 向其他服務取資料的呼叫，我推測是 carts，但 log 沒寫目標 URL。
- **時間順序有落差。** orders 的 503 比 12:44 早約 1 分鐘（12:43:01），carts 指標跳升在 12:44 前後。我只用約 80 秒間隔取樣看時間序列，無法精確判斷 carts 與 orders 誰先。
- **payment 是第二候選，證據偏弱。** `payment_container-sockets` 2.96 → 5.15（在基準期標準差下變化最顯著，約 6.5σ），但絕對值很小，記憶體也只多約 1 MB。
- **carts-db 可能是被動受害者，也可能是真正源頭。** 它的 sockets 重置可能是 carts 重連造成的，也可能是 DB 自己重啟。我沒有看到 carts-db 的 log 錯誤，所以無法分辨。
- **queue-master 的 error log 量很大，但事發前後差不多**（2685 vs 2444 筆），判斷是背景雜訊。
- 事發時間我以 12:44 對應 epoch 1732452240 估算，可能有數十秒誤差。

```json
{"root_cause_service": "carts", "top3": ["carts", "carts-db", "payment"], "evidence": ["carts warn/error logs 事發前 23 筆 -> 事發後 668 筆（每 2 分鐘約 120-135 筆），含 PageNotFound: Request method 'POST' not supported", "carts memory working set 約 330MB -> 580-674MB 峰值，之後回到約 345MB；carts sockets 約 20 -> 峰值 70，之後穩定約 30", "carts-db sockets 16 -> 3 -> 26，顯示連線重置", "orders 自 12:43:01 起出現 503 Service Unavailable（AsyncGetService.getDataList），-1 分鐘 64 次；front-end 對應 500 IllegalStateException", "payment sockets 2.96 -> 5.15，偏離基準最大（約 6.5σ）但絕對值很小"], "uncertain": ["orders 的 503 呼叫目標未在 log 中確認是 carts", "orders 503 比 12:44 早約 1 分鐘，與 carts 指標跳升的先後順序未能精確判定", "carts-db 是被動受害者還是真正源頭（未見其 log 錯誤）", "payment 的 sockets 變化是否有實際影響", "事發時間以 12:44 估為 epoch 1732452240，可能有數十秒誤差"]}
```