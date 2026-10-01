## 查核結果(order_id `live-20261001-02-complete`)

**範圍**:datasource `day17-loki`、`lab_case=complete`、版本 `delivery-hardening-local-r2`(local Docker 教學環境)。服務為 order-api 與 notification-receiver。

### 1. 程式與設計(唯讀)
- `src/Program.cs:79-88`:`transitioned` 為 true 時建立 Notification(`Guid` 作 notification_id),寫入 Channel,接著在第 92 行寫 `cancel` log。
- `src/Program.cs:257-261`:Worker 收到接收端 2xx 才寫 `notify_sent`。`notify_sent` 只代表 HTTP 回應成功,是發送端觀察。
- `design/design-review.md` 第 1 點:Worker 送達與 HTTP 回應沒有固定先後,所以 log 時間順序不能當因果證據。
- 程式檔沒有標示版本字串。`VERSION` 要到執行期才由 log 的 `version` 欄位確認,見下一節。

### 2. Log 查詢
| # | 條件 | 結果 |
|---|---|---|
| A | `list_loki_label_names`(datasource `day17-loki`) | **未獲授權,沒有執行**,也沒有重試。不影響後續查詢。 |
| B | 起訖帶微秒的時間戳 | 工具回報解析錯誤,原文為 `unexpected tDIGIT`。 |
| C | `{lab_case="complete"} \|= "live-20261001-02-complete"`,2026-09-30T19:26:22Z 到 19:26:24Z,forward,limit 50 | 回傳 3 行,沒有截斷。 |

查詢 C 的起訖時間比 task.json 的 19:26:22.525875Z 到 19:26:23.768514Z 各外擴不到 1 秒,因為工具不接受微秒格式。三行都落在 task 時間窗內。

**回傳的三行:**
1. order-api、`/logs/complete/api/logs.jsonl`:`event=cancel`、`result=ok`、`transitioned=true`、`refund_requested=true`、`notification_id=3b30d36ba5a64e7c9ea01ea02cc61074`、`version=delivery-hardening-local-r2`。
   - 時間為 2026-10-01T03:26:23.229+08:00,等於 UTC 19:26:23.229。
2. order-api 同檔:`event=notify_sent`,notification_id 相同。
   - 時間為 UTC 19:26:23.280。
   - 沒有 `sync` 欄位,所以走的是非同步 Worker 路徑。
3. notification-receiver、`/logs/complete/receiver/logs.jsonl`:`event=notification_received`。
   - notification_id、order_id、request_id、run_id 都與發送端一致。
   - `kind=order_cancelled`、`refund_requested=true`、`attempt=0`。
   - 時間為 UTC 19:26:23.2756。

### 3. 比對
- **API 結果**:取消成功(轉換成功),並建立通知。
- **發送端**:有 `notify_sent`,沒有 `notify_deferred`、`notify_attempt_failed` 或 `notify_dead_letter`。
- **接收端**:有獨立來源的 `notification_received`,ID 與 payload(含 `refund_requested=true`)都一致,`attempt=0` 表示首次送出就被接收。
- 接收端時間(…23.2756)早於發送端 `notify_sent`(…23.2797),與設計所說「送達與回應順序不固定」一致,不構成矛盾。

### 4. 未知與限制
- 我只用 order_id 做字串比對。若接收端另有只含 notification_id 而不含 order_id 的重複紀錄,這次查詢看不到。本次沒有這類資料的跡象,也沒有另查,以免擴大範圍。
- 只確認 log 內容,沒有查接收端的下游處理或業務結果。
- 標籤名稱清單(A)未取得,所以沒有對標籤的完整性做確認。

```json
{
  "order_id": "live-20261001-02-complete",
  "sender_status": "notify_sent (notification_id 3b30d36ba5a64e7c9ea01ea02cc61074, async worker, no failure/deferral/dead_letter events)",
  "receiver_status": "confirmed",
  "missing_sources": [
    "list_loki_label_names 未獲授權,未取得標籤清單",
    "未以 notification_id 單獨查詢接收端重複紀錄"
  ],
  "next_action": "無需補送。若要排除重複接收,請在同一 datasource 與 lab_case 下,用 notification_id 另查 notification-receiver。是否結案由操作者決定。"
}
```