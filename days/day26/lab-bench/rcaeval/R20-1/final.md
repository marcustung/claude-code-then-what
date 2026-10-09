**結論：根因最可能是 `user` 服務。** 事發前後只有它的 CPU、記憶體、socket 和延遲同時出現明顯異常。

**方法：** 以 20:25 UTC（epoch 1705782300）切成前後兩段。事發前的資料當基準，計算每個指標的 (後均值 − 前均值) / 前標準差。

**證據**
- **延遲：** `user_istio-latency-95` 事發前約 0.0097 s，t≈-7 s 時已升到 0.36 s，之後多在 0.36–0.7 s。事發前後均值是 0.021 → 0.484 s，z≈8.9。`user` 的 p99 是 0.066 → 0.992 s。
- **CPU：** `user_container-cpu-usage-seconds-total` 的序列值事發前約 1.1–1.3，t≈-7 s 起跳到約 40，之後一直維持在那裡。
- **記憶體與連線：**
  - 記憶體：`user` 的 working-set 事發前緩升，約 5.6 → 7.1 MB。t≈-7 s 掉到 2.9 MB，之後在 1.2–8.4 MB 間反覆，多次剛好停在 8388608（正好 8 MiB）。均值 2.85e7 → 5.13e8 的 z=5.1 與這些序列值不一致，原因我沒查清。
  - 連線：`user_container-sockets` 15 → 33（z=5.9）。`user-db` 的 sockets 也從 7.8 → 15.6（z=7.4）。
- **下游症狀：** `front-end_istio-latency-95` 約 0.09 → 0.31–0.64 s，p99 是 0.17 → 1.13 s。`user` 的延遲與 CPU 在 t≈-7 s 就已異常，與 front-end 同時；我沒做逐秒的先後比對。
- **user 的 log 沒有異常：** log 量穩定在每分鐘約 500–630 行，我沒有看到錯誤訊息。我只算了行數，沒有檢查 `took=` 的耗時。

**其他候選與為何排除**
- **queue-master（第 2 名）：**
  - log 有大量錯誤：`RetryExec : I/O exception` 約 3600 筆，`DockerSpawner : Exception trying to launch` 約 1200 筆。
  - 這些錯誤從 20:11 就開始，也就是事發前的基準期就有，所以更像是原本就存在的雜訊，不是這次事件的原因。
  - 錯誤量在 20:10 / 20:20 / 20:30 三個 10 分鐘區間是 1984 / 2444 / 1416，沒有在 20:25 之後跳升。
- **catalogue（第 3 名）：** p99 約 0.009 → 0.059 s（z=10.7），但 p90 只從 0.0047 變到 0.0050，幅度很小，比較像被連帶影響。`catalogue-db` 的記憶體 z 值雖高，但絕對變化不到 1%（2.171e8 → 2.174e8）。
- **carts：** log 只有 `UnknownHostException: zipkin`（57 筆），是 tracing 的警告，從 20:11 就有，與事件無關。
- **node memory-active-bytes：** 數值 7338 → 2.1e6（z=1316）。這很可能是指標單位或採集異常，我沒有採信。

**不確定之處**
- 我沒有確認 `user` 本身是原因還是被別的東西打爆，例如 user-db、或 CPU/記憶體限制被設得很低（記憶體多次卡在 8 MiB 附近，疑似有限制）。
- 時間粒度是 1 秒，但三個服務的異常都出現在 t≈-7 s，無法分出誰先誰後。
- 前面的 z 值是以事發前序列的標準差為單位。若基準段很平穩，標準差很小，z 值會被放大。
- log 沒有 request 層級的錯誤碼，所以「操作失敗」只能從延遲推測，沒有直接證據。

```json
{"root_cause_service": "user", "top3": ["user", "queue-master", "catalogue"], "evidence": ["user_istio-latency-95 均值 0.021→0.484 s (z≈8.9)，p99 0.066→0.992 s", "user cpu-usage 序列值 事發前約1.1-1.3，t≈-7s 起約40", "user memory working-set 事發前緩升至約7MB，之後在1.2-8.4MB反覆並多次停在8388608", "user sockets 15→33，user-db sockets 7.8→15.6", "front-end p95 0.09→0.31-0.64 s、p99 0.17→1.13 s", "queue-master 錯誤 log 從 20:11 就開始(RetryExec 3600筆、DockerSpawner 1200筆)，屬基準期雜訊"], "uncertain": ["user 是根因或被 user-db/資源限制拖垮", "user、front-end、catalogue 異常都在 t≈-7s，無法分先後", "user 記憶體均值 5.13e8 與序列值(≤8.4MB)不一致，原因未查明", "z 值受基準段標準差大小影響", "log 無 request 錯誤碼，失敗只能由延遲推測", "node memory-active-bytes 異常疑為指標問題，未採信"]}
```