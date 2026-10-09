我寫好 `reconcile.py`,也對 `data/` 三輪各跑了一次,結果在 `out/view.json` 和 `out/index.html`。結論是:今天先查 `missing-notification-20260921-193704` 這一批。`data/` 和 `notification-contract.md` 都沒改。我只讀了 `data/` 和目前目錄,沒讀父目錄。我沒有開 `index.html` 看畫面,只確認檔案已產生。

## 分母怎麼定
- **應完成數**:`requests.jsonl` 裡 HTTP 2xx 且 `transitioned=true` 的取消請求,也就是契約 NC-01 說的「唯一成功轉換」。重複取消、已出貨被拒(409)、404、401 都不算。
- **交叉檢查**:`logs.jsonl` 的轉換集合和 `metrics.txt` 的 `oc_transitions_total` 都要和這個分母一致。不一致就判 unknown,因為分母不可信。

## 怎麼比對
- **已確認完成**:`receipts.jsonl` 是接收端收據。我用 `request_id` 對回分母,同時要求 `run_id` 和 `order_id` 都吻合,並以 `notification_id` 去重。
- **服務自報不算證據**:`oc_notify_sent_total` 只拿來交叉檢查,不算送達(NC-04)。
- **其他 run 的收據**:排除不計。
- **有 `dead_letter` 就判 investigate**:log 有 dead_letter 事件或 `oc_notify_dead_letter_total` 大於 0。
- **同一 request 收到兩則不同通知**:判 investigate(違反 NC-01)。
- **收據對不到任何成功轉換**:判 investigate(違反 NC-02/03)。
- **入佇列數少於轉換數**:判 investigate。

## 各狀態的判定
- **matched**:每筆都有收據。
- **investigate**:有上述異常;或佇列深度為 0、沒有 dead_letter,但仍有缺收據的事件。
- **waiting**:有缺收據的事件,佇列深度大於 0,而且沒有 dead_letter 或失敗紀錄。
- **unknown**:缺 `requests.jsonl` 和 `logs.jsonl`;缺 `receipts.jsonl`;分母來源互相矛盾;或有缺收據的事件但沒有佇列深度,分不出是還在送還是已遺失。
- **數字寫 null**:unknown 時,無法判斷的數字寫 null,不補 0。

## 每輪結果

| run | expected | received | unmatched | status | 依據 |
|---|---|---|---|---|---|
| missing-notification-…193704 | 9 | 3 | 6 | **investigate** | 佇列深度 0、沒有 dead_letter,但 6 筆沒有收據(o-01、02、04、05、07、08)。log 有這 6 筆的 `notify_deferred`,之後沒有 `notify_sent`。服務自報 `sent=9`,接收端只收到 3 則,所以它的計數不可信。 |
| missing-notification-…193835 | 9 | 9 | 0 | **matched** | 9 筆都有收據。log 裡有 45 次 deferred,但最後都送達了。 |
| slow-sync-control-…191636 | 259 | 12 | 247 | **waiting** | 佇列深度 253,沒有 dead_letter 或失敗紀錄,收據仍在陸續進來(間隔約 150 ms,與 `OC_SINK_DELAY_MS=150` 吻合)。 |

## 還不確定的地方
1. **slow-sync 的 manifest 寫 `terminal`,但資料顯示還沒送完。**
   - 它沒有 `last_queue_depth`,`wait` 也只有 timeout,沒有 terminal 條件。
   - 整輪只跑 7 秒,以每則約 150 ms 估計,259 則要約 39 秒才送完。
   - 我認為 manifest 的 `terminal` 不能當作已完成的證據,所以判 waiting。
2. **slow-sync 的 waiting 只是擷取當下的狀態。**
   - 這份快照是 2026-09-23 的,距今已 15 天,不會再變。
   - 要確定它有沒有送完,得重新擷取目前的收據,否則只能維持 waiting。
3. **slow-sync 的 metrics 和收據時間點不同步。**
   - metrics 寫 `sent=5`,收據卻有 12 則,表示 metrics 擷取得比收據早。
   - 253 這個佇列深度同樣是較早的值,所以我把它當作「還沒清空」的跡象,沒有拿它算精確數字。
4. **missing-notification 那 6 筆遺失的原因我推不出來。**
   - 我只確定「佇列清空後仍沒有收據」。為什麼 deferred 之後沒有 sent,要看服務程式或 `faults` 設定。
   - `notification_id` 是取自服務 log,不是接收端的證據。
5. **契約狀態仍是 `proposed`。**
   - 我把它當判定依據,但作者還沒接受,規則之後可能會改。

檔案都在目前目錄的 `reconcile.py` 和 `out/` 底下。