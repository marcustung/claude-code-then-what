## 呼叫路徑(取消回應 → 通知送達)

1. `POST /orders/{id}/cancel` 進入 handler:`src/Api/Program.cs:48`
2. 呼叫 `store.TryCancel` → `Cancellation.Cancel`(`src/Domain/Cancellation.cs:8-22`),`Transitioned` 判斷是否要通知(`Cancellation.cs:25`)
3. 若 transitioned,建立 `Notification` 並寫入 unbounded `Channel`:`Program.cs:81-87`(本次兩組皆非 `SyncNotify`,走 `channel.Writer.WriteAsync`,`Program.cs:87`)
4. HTTP 回應在此時就完成並回傳(`Program.cs:89-92`),與通知送達**非同一時序**——回應不等待通知結果
5. 背景服務 `NotificationWorker.ExecuteAsync`(`Program.cs:224-267`)以 `await foreach` 單一迴圈從 channel 逐筆取出
6. 每筆呼叫 `await _http.PostAsync(_sink, ...)`(`Program.cs:246`)送到 fake sink,成功則 `notify_sent`(`Program.cs:258-259`),失敗則重試(200/400/800ms backoff)或進 `notify_dead_letter`(`Program.cs:261-264`)

## 已確認事實
- `NotificationWorker` 是**單一 `BackgroundService` 實例**,`await foreach` 為序列迴圈,沒有平行 worker 或批次分派(`Program.cs:224-266`)。
- 迴圈內 `await _http.PostAsync(...)`(`Program.cs:246`)會**阻塞**同一輪迭代直到 HTTP 回應或逾時,即通知處理是**序列且等待 HTTP**,佐證見 slow/logs.jsonl 中 `notify_sent` 時間間隔穩定落在約 0.30–0.31 秒(如第310–329行)。
- control 組 sink_delay_ms=0(control/report.json:18),`notify_sent` 幾乎緊跟在對應 `cancel` 之後(control/logs.jsonl:2-5,間隔數十毫秒),201 transitions/201 receipts/201 sent 全部吻合(control/report.json:33-35)。
- slow 組 sink_delay_ms=300(slow/report.json:18),`queue_depth` 隨 cancel 請求持續累積(slow/logs.jsonl:2-40,從0升至20+),截至檔案結束(slow/logs.jsonl:329,ts 19:32:59.187)僅完成127筆 `notify_sent`,與 slow/report.json:34-35 的 receipts=127、sent=127 一致。
- k6 門檻(control/k6-summary.json、slow/k6-summary.json)顯示 `cancel_ms` p95 分別為5.99ms與13.37ms,遠低於250ms,`http_req_failed` 皆0,checks全過——因為API層在寫入 channel 後立即回應(`Program.cs:89`),與通知背景送達解耦,故API門檻不受300ms sink延遲影響。
- slow 組 `receipts_match_transitions_once=false`(slow/report.json:30),transitions=201但receipts僅127(slow/report.json:33-34)。
- plan.md:6 明確標註300ms為人為注入延遲、非production量測;plan.md:8明確標註20秒為教學觀察截止,非SLA,截止時缺收據代表「截止未完成」而非「證實遺失」。

## 推論(未逐行量測但可合理支持)
- 序列送出+300ms/筆的節奏,使 worker 理論吞吐上限約3.3件/秒,而10件/秒的取消請求持續20秒共產生201件轉換,超出視窗內worker可完成量,導致積壓——此為slow組截止時只完成127件的主要機制性解釋,而非單一請求逾時或sink拒絕。
- 74筆(201-127)在快照當下應仍停留在channel佇列或正在等待送出/重試中,而非必然遺失,因為程式沒有丟棄邏輯(僅`notify_drop_over_queue`故障有Deferral路徑,而本次faults均未載入,見兩組logs.jsonl的`startup`行`faults_loaded:false`)。

## 尚缺量測(建議下一步查核,非本次可判定)
1. **service程序是否在截止後仍存活繼續消化佇列**:目前只讀到logs.jsonl結尾(slow第330行為空),需確認是否有「stop service at cutoff」的明確標記事件、以及stop的實際wall-clock時間點,才能界定「截止快照」與「關閉後日誌」的邊界,避免用快照後才寫入的log筆數誤判為截止時完成量。
2. **剩餘74筆通知ID的最終狀態**:比對receipts.json全量(目前僅抽樣前30、offset 610附近)與logs.jsonl中是否存在對應的`notify_sent`/`notify_attempt_failed`/`notify_dead_letter`事件,逐ID核對而非只看總數。
3. **channel實際剩餘深度**:若有`/metrics`快照(`oc_notify_queue_depth`,Program.cs:137)在截止當下的值,可直接佐證積壓筆數是否與201-127=74吻合。
4. **worker是否在收到停止訊號時中斷了正在進行的PostAsync**:需查是否有`OperationCanceledException`相關的log事件,以判斷是「還沒輪到」還是「處理到一半被中斷」。