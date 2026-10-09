Dashboard 的第一版已經推上去,但我改了日誌查詢後再推第二版時被擋(403)。我也沒辦法再讀回線上的 Dashboard,所以不知道線上現在是不是第一版。我沒有換帳號或用別的方式繞過,需要你確認權限。

## 目前狀態
- **本機檔案**:`dashboard.json` 是最新版,UID 是 `day25-work-view`,標題是「取消訂單通知:待辦工作視圖」。`gcx resources validate` 通過。
- **第一版**:`validate`、`--dry-run` 和 push 都成功。
- **第二版**:push 回 `403`。之後 `gcx resources get dashboards/day25-work-view` 也回 `403`,所以線上內容我無法確認。第一次能寫、第二次不能,原因我不清楚(token 或權限變了?),請你查一下。
- **視覺檢查沒做到**:`gcx dashboards snapshot` 回 HTTP 500,疑似沒有 image renderer,我沒查證。我沒看過任何截圖,版面和表格欄位合併、顏色對應是否正確都還沒驗證。
- **資料夾**:`gcx resources get folders` 回空清單。我沒指定資料夾,所以第一版推到了預設位置(General)。

## 資料探索
`job="day25-work-view"` 有四個對帳指標:
- `work_expected`、`work_matched`、`work_unmatched`
- `work_status`:`status` 標籤有 matched、investigate、unknown 三種,另有 `reason` 標籤

輪次標籤是 `run`:

| run | 情境 | 應完成 | 確認完成 | 狀態 |
|---|---|---|---|---|
| `d24-normal` | Day 24 正常接收端 | 9 | 9 | matched |
| `d24-slow` | Day 24 慢接收端 | 9 | 9 | matched |
| `sep-fixed` | 修正版同情境 | 9 | 9 | matched |
| `sep-missing` | 原版漏通知 | 9 | 3 | investigate |
| `sep-slow` | 慢接收端(觀察未結束) | 259 | 12 | unknown |

Loki 的事件日誌帶 `run`、`state`、`order_id`、`notification_id`、`request_id`。

## 各面板
1. **怎麼讀這張圖**(文字):說明「完成」和「完成率」的定義。
2. **各輪對帳**(表格):每輪一列,有應完成、確認完成、未完成、完成率、狀態、原因,另有 `$run` 輪次下拉可篩選。
   - 用 `work_expected`、`work_matched`、`work_unmatched`、`work_status`。
   - 狀態 unknown 的輪次,完成率顯示「資料不足」(灰色),不補 0%,也不給綠燈。
3. **未完成事件清單**(Loki 日誌):`state=unmatched` 且有真實通知 ID 的事件,是「先查這批」的清單。
4. **資料不足的事件**(Loki 日誌):缺通知 ID 或狀態 unknown 的事件,要先補資料才能判斷。

## 查詢驗證
我用 gcx 跑了面板 2、3、4 的查詢,結果合理。我沒有跑面板 2 的 A、B、D、E 單獨查詢,也沒驗證表格轉換後的呈現。
- **完成率**:`d24-normal`、`d24-slow`、`sep-fixed` 是 100%,`sep-missing` 是 33.3%(3/9),`sep-slow` 因為是 unknown 而被排除。
- **面板 3**:`sep-missing` 有 42 筆。這是 6 小時內的計數,同一事件被重複發布,所以大於 6 個未對上事件,清單已用 `dedupStrategy: exact` 去重。
- **面板 4**:`sep-slow` 有 1736 筆,同樣是重複發布的結果。
- **對帳驗算**:expected = matched + unmatched 在每一輪都成立(3+6=9、12+247=259)。

## 為什麼這樣算完成率
完成率是 `work_matched ÷ work_expected`,因為契約 NC-04 規定「送達」以接收端收據為準。`sep-slow` 的觀察還沒結束,而且 247 筆未對上的事件通知 ID 是 None,不能說它們失敗了,所以只標「資料不足」。

## 刻意沒用的指標
- `sender_reported_sent`:是寄送端自己回報,不算送達證據。`sep-slow` 裡它是 5,但對上的收據是 12,兩者對不起來。
- `notification_queue_wait_milliseconds_*`、`traces_*`、`otelcol_*`、`up`:延遲和基礎設施指標,回答不了「哪批還沒完成」。

## 還不確定的地方
- 面板 3、4 的 LogQL(`notification_id!="unknown"` 和 `state="unknown" or notification_id="unknown"`)只用 `gcx datasources loki query` 驗證過。這兩個新版查詢是否已在線上 Dashboard 生效,取決於上面的 403 問題。
- `sep-slow` 的 247 筆事件最後會變成完成還是失敗,要等觀察結束。
- 資料是一次性重播,不是持續寫入。我用 `last_over_time(...[$__range])` 取最後值,避免超過 5 分鐘後面板變空。如果時間範圍拉到資料出現之前,面板會空。
- `work_status` 目前每輪只有一個 `reason`,我預設每輪就一個。

## 建議的下一步
你確認 token 的 Dashboard 寫入權限和資料夾後,我再重新 push 並重新截圖(或改用別的 renderer)。需要我指定資料夾的話,請給我資料夾 UID。