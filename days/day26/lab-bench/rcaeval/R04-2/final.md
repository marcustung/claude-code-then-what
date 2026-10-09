**根因服務：adservice**，信心高。它在 04:51:53 UTC 重啟，之後持續拋 NullPointerException。重啟的原因在資料裡看不出來。

**證據**

1. **adservice 重啟。** 事發時間 04:52:00 UTC 取 epoch 1731905520。adservice 的 log 有以下順序：
   - `1731905513 *** shutting down gRPC ads server since JVM is shutting down`，接著是 `*** server shut down`。
   - `1731905518 AdService starting.`，接著是 `1731905519 Ad Service started, listening on 9555`。
   - 重啟前每秒都有 `received ad request` 正常紀錄。

2. **重啟後 adservice 開始報錯。**
   - 從 `1731905521` 起出現 `SEVERE: Exception while executing runnable io.grpc.internal.ServerImpl$JumpToApplicationThread...` 和 `java.lang.NullPointerException: Cannot invoke "java.util.Collection.toArray()"...`，各 1741 筆。
   - 事發前這兩種 log 都是 0 筆。
   - 最後一筆在 `1731906223`，也就是資料尾端，所以到資料結束時還沒恢復。

3. **frontend 的失敗來自 adservice。**
   - `failed to retrieve ads` 事發後有 1746 筆，事發前只有 17 筆。
   - 那 17 筆從 `1731905514` 開始，正好落在 adservice 關閉到啟動的空窗，早於 adservice 重啟後的第一筆 NPE（`1731905521`）。
   - trace 裡 frontend 的 statusCode 非 0 的 span，事發前 17 筆（空值），事發後 1746 筆（2.0 有 1740、4.0 有 16、14.0 有 7）。
   - 錯誤 span 只出現在 frontend，其他服務都是 0。
   - frontend 的 `failed to retrieve ads`（1746）與 adservice 的 NPE（1741）幾乎一對一。

4. **其他服務沒有受影響。**
   - 各服務 trace 延遲的中位數事發前後幾乎沒變：
     - frontend 3418 → 3373 µs
     - checkoutservice 3341 → 3290
     - recommendationservice 3600 → 3565
     - productcatalogservice 5.0 → 5.0
     - currencyservice 101 → 100
   - 所以「變慢」比較像使用者看到的廣告載入失敗，不是下游延遲升高。
   - 除 adservice 外，沒有其他服務在 log 出現 error 或 exception。

5. **metrics 只有很弱的佐證。**
   - 事發前後差異超過 3 個標準差的欄位，大多是 memory limit 這類設定值的微小變動，沒有意義。
   - 唯一與 adservice 相關的有意義訊號是 `adservice_istio-latency-95`，從 0.0059 升到 0.0131，約 3 個標準差以上。
   - `adservice_istio-error-total` 的平均值從 0 升到 0.014，數值極小。

**前 3 名**
1. adservice：重啟後持續 NPE，是最先出問題的服務。
2. frontend：錯誤都落在它身上，但它是受害者，不是原因。
3. 第三名沒有實質證據。redis、cartservice 等的 log、trace 和 metrics 都沒有異常，我只是湊數，不建議當作候選。

**不確定的地方**
- adservice 為何在 04:51:53 關閉，資料裡看不出來。可能是人為或排程重啟、部署，或被 OOM 殺掉，但我沒有看到 OOM 或 restart 次數的指標，無法判斷。
- NPE 是重啟後才出現，可能是新版本或設定有 bug，也可能是它依賴的資料沒載入，這點也無法確認。
- adservice 沒有任何 trace span，所以無法用 trace 驗證它的延遲，只能靠 log 和 istio 指標。
- 我用 04:52:00 當事發點。frontend 的第一批失敗在 04:51:54，比回報時間早約 6 秒。

```json
{"root_cause_service": "adservice", "top3": ["adservice", "frontend", "無其他有證據的候選（redis/cartservice 無異常）"], "evidence": ["adservice log 1731905513 'shutting down gRPC ads server since JVM is shutting down'，1731905518 'AdService starting'", "adservice 重啟後 NullPointerException 1741 筆、SEVERE 1741 筆，事發前 0 筆，持續到資料尾端 1731906223", "frontend 'failed to retrieve ads' 事發後 1746 筆（事發前 17 筆，從 1731905514 開始）", "trace 錯誤 span 只在 frontend：事發後 1746 筆（2.0:1740、4.0:16、14.0:7），其他服務 0 筆", "各服務 trace 延遲中位數事發前後幾乎不變（frontend 3418→3373µs）", "adservice_istio-latency-95 從 0.0059 升到 0.0131"], "uncertain": ["adservice 重啟的原因（部署、人為、OOM）資料中看不出來", "NPE 的直接成因（新版本 bug 或依賴資料缺失）無法確認", "adservice 沒有 trace span，無法用 trace 驗證其延遲", "第 2、3 名候選缺乏證據，frontend 僅為受害者", "事發時間以 04:52:00 估算，frontend 最早失敗在 04:51:54"]}
```