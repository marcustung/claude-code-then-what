## 結論

最可能的根因是 **front-end**,但證據偏弱,信心中等偏低。

### 資料限制
- `traces.csv` 只有表頭,沒有任何呼叫鏈資料,無法用 trace 追上下游。
- `metrics.csv` 共 1441 筆,每秒一筆,涵蓋 20:05:42 到 20:29:42。
- `logs.csv` 共 87396 筆。

### 證據
1. **front-end 容器在 20:18 被 SIGTERM 終止,比回報時間 20:19 早約一分鐘。**
   - log 在 `timestamp=1732393085`(約 20:18:05)出現:
     - `npm ERR! signal SIGTERM`
     - `npm ERR! command sh -c -- node server.js`
     - `npm timing npm Completed in 820021ms`
   - 該程序從 20:04:25 跑到 20:18:05,約 820 秒。
   - 5 秒後(`1732393090`)又出現一次相同的 SIGTERM 錯誤。
   - 這些是整份 log 中唯一的服務終止紀錄。
2. **front-end 換了 pod。**
   - log 裡有三個 pod:`front-end-f77549869-mpnfq`(23803 筆)、`front-end-5f6d88487b-fvx7x`(22181 筆)、`front-end-f77549869-nwglb`(63 筆)。
   - 兩個 ReplicaSet hash 不同,看起來是 rollout 或重建。
3. **front 的 metrics 在同一時間消失。**
   - `front_container-*` 共 8 個欄位,從第 779 列(約 20:18:41)起到最後(第 1440 列)全部為空,共 662 筆。
   - 在此之前,`front_container-network-receive-bytes-total` 穩定在約 3.7 萬。
   - 其他服務沒有這種持續性缺值。`catalogue`、`carts-db`、`catalogue-db`、`session-db` 只各缺 1 到 3 筆,屬於單點缺漏。
4. **前後 log 量的差異。**
   - 各服務每分鐘 log 量(前端約 1900 筆,user 約 600 筆)在 20:19 前後都沒有明顯下降。
   - 以 log 量看不出服務中斷。

### 次要候選(證據更弱)
- **queue-master / rabbitmq**:
  - `queue_container-network-receive-bytes-total` 在第 878 到 894 列約為 6039,第 895 到 907 列升到 9344(約 20:20:37 起),之後回到約 4767。
  - 基準值約 400 到 600,所以放大約 10 到 15 倍,是整份 metrics 中最明顯的突增。
  - 以事前標準差算的 z 值最高(約 5.0),但上升的時間在 20:19 之後,較像下游症狀。
  - 它的 log 每分鐘 200 筆以上,內容是 `DockerSpawner : Spawning new container` 和 `RetryExec : Retrying request to {}->unix://localhost:80`,但事發前就持續出現,所以我判斷是背景噪音。
- **orders-db / carts-db**:
  - 兩者在 20:20 都出現 `Deprecated operation requested` 警告。
  - 這類警告看起來是一般的驅動程式相容性提示,可能無關。

### 不確定之處
- 無法分辨 front-end 被終止是根因(例如 OOM 或 liveness 失敗),還是正常 rollout。
- 沒有看到 front-end 重啟前的資源異常:我只檢查了前 40 個變動最大的指標,沒有針對 front-end 的記憶體或 CPU 逐項檢查。
- 20:24 有一個 front-end 的 406 錯誤高峰(111 筆,平時每分鐘 20 到 30 筆),我沒有深入追查原因。
- 「Order response 406」在事發前就有,屬於基準噪音。
- 第 2 名和第 3 名的排序主要靠異常幅度,不是因果證據。

```json
{"root_cause_service": "front-end", "top3": ["front-end", "queue-master", "orders"], "evidence": ["front-end log 在 ts=1732393085(約20:18:05)出現 'npm ERR! signal SIGTERM' / 'npm ERR! command sh -c -- node server.js',程序已執行約820021ms,5秒後再出現一次", "front-end 有 front-end-f77549869-* 與 front-end-5f6d88487b-fvx7x 兩個 ReplicaSet 的 pod,疑似重建或 rollout", "front_container-* 共8個欄位自第779列(約20:18:41)起至結尾共662筆為空;之前 network-receive-bytes-total 約3.7e4", "queue_container-network-receive-bytes-total 從基準約400~600升到6039,再到9344(第895~907列,約20:20:37起),約10~15倍,為時間上較晚的突增", "traces.csv 僅有表頭,無呼叫鏈資料"], "uncertain": ["無法判斷 front-end 被 SIGTERM 是故障(OOM/liveness)還是正常 rollout", "沒有逐項檢查 front-end 重啟前的記憶體與 CPU", "queue-master 的網路突增發生在 20:19 之後,可能是下游症狀,也可能是獨立問題", "orders 排第3名僅因網路與記憶體有輕微變動(z約3.2與-2.6),證據薄弱", "20:24 前端 406 錯誤高峰(111筆)原因未查", "沒有 trace 資料,無法驗證因果方向"]}
```