# 通知查核：r2-healthy-01（本機教學封存，非正式環境）

Skill 工具沒有登錄 `trace-notification`，所以我直接讀 `SKILL.md`，照它的步驟做。`evidence.json` 已存在。我沒有執行 `collect.py`，改用 `data/` 原始檔逐筆核對，兩邊一致。

## 1. 資料身分與版本
- `task.json` 的版本是 `delivery-hardening-local-r2`。`data/logs.jsonl:1`（startup）到 `:4` 的 version 都相同。
- startup 顯示 `faults_loaded:false`（`logs.jsonl:1`），所以這次沒有注入故障。
- `logs.jsonl` 和 `receipts.json` 都在，`missing_sources` 是空的。
- `src/Program.cs:13` 的版本來源是 `VERSION` 檔或環境變數。我看不到部署當下的 `VERSION` 檔，所以只能說 log 記的版本相符，不能說執行檔本身相符。

## 2. API 結果
- `logs.jsonl:2`：`cancel`、`result:"ok"`、`transitioned:true`、`refund_requested:true`。
- 這筆 log 帶有 `notification_id=7e746d20853d48b9b3948c1fe92319c1`，`order_id=r2-healthy-01`，`request_id=r2-healthy-request`。
- 對應程式：`Program.cs:72` 判定有狀態轉換，`:82-88` 建立通知並放入 channel，`:92` 寫 log。
- 退款判斷在 `Cancellation.cs:19`（已付款且尚未取消才退款），和 `refund_requested:true` 相符。
- `logs.jsonl:4` 是另一張單 `r2-shipped-01`：`rejected_shipped`，`notification_id:null`。它跟本單無關，而且符合「已出貨不通知」（`Program.cs:74`）。

## 3. 發送端觀察
- `logs.jsonl:3`：`notify_sent`，`notification_id` 與上面相同。
- 這筆由 worker 寫出（`Program.cs:257-260`）。程式邏輯是 HTTP POST 回成功狀態才會寫 `notify_sent`（`:248`）。
- 沒有 `notify_attempt_failed`、`notify_deferred`、`notify_dead_letter`。
- 發送端狀態：`sent`。這只代表發送端觀察到成功。

## 4. 接收端佐證
- `receipts.json` item 0（`receipts.json:2-15`）：`status:200`，`notification_id`、`order_id`、`request_id` 都與 log 相同，`kind:order_cancelled`，`refund_requested:true`，`attempt:0`。
- 只有這一筆收據，沒有重複投遞。
- 時間先後合理：cancel log 在 `…10.8209`，收據在 epoch `1790646010.8578`（換算約 09:40:10.858+08:00），`notify_sent` 在 `…10.8613`。
- 因為有對應的收據來源，接收端標 **confirmed**。

## 5. 限制
- 收據來自本機 fake sink 的封存，不是正式接收端。這只證明本機教學情境。
- `design-review.md:4` 說 FakeSink 未保存 `refund_requested`，但這份收據有這個欄位，兩者不一致。收據內容不能當作 payload 從未被改動的證明。
- `design-review.md:3` 的行號（API:69、79、84、88、89）和現行 `Program.cs` 不符。現行是 `:64` 到 `:93`，我以現行行號為準。
- 設計文件 `:9` 寫本輪沒有跑 .NET。單元、HTTP、payload 和重送順序的測試都還沒執行，這份結論只來自 log 和收據對照。
- 我沒有修改檔案，也沒有補送、結案或宣告團隊接受。

## 下一步
沒有缺件，不需要補送。若要更完整，可請操作者依 SKILL 固定入口執行 `collect.py`，確認 `evidence.json` 是腳本產生的。另外請確認 FakeSink 是否保存 `refund_requested`，並確認部署的 `VERSION` 檔內容。

```json
{
  "order_id": "r2-healthy-01",
  "sender_status": "sent (notify_sent observed at data/logs.jsonl:3, notification_id 7e746d20853d48b9b3948c1fe92319c1)",
  "receiver_status": "confirmed",
  "missing_sources": [],
  "next_action": "無需補送。可選：操作者執行 collect.py 重新產生 evidence.json；確認 FakeSink 是否保存 refund_requested，以及部署 VERSION 檔內容；design-review 的行號待依現行 Program.cs 更新。"
}
```