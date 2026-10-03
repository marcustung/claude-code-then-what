**固定檢查未執行，結果停在待查（NEEDS_FOLLOWUP）。** `collect.py` 和 `gate.py` 的 Bash 執行都需要核准，這次沒有取得。所以我拿不到合法的 `records[].ref`，也沒有自編。

## 範圍
- 訂單 `r2-healthy-01`，版本 `delivery-hardening-local-r2`。
- 環境是本機教學 fixture，不是正式環境。
- 沒有連 Log server。

## 查到的內容（直接讀檔，未經 collect.py）
1. **API／發送端**：`data/logs.jsonl` 第 2 行是 `cancel`，結果 `ok`，`transitioned=true`，`refund_requested=true`，`queue_depth=1`。通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`。
2. **發送端觀察**：同檔第 3 行是 `notify_sent`，通知 ID 和訂單 ID 都相符。
3. **接收端佐證**：`data/receipts.json` 有 1 筆收據，status 200。payload 的 `notification_id`、`order_id` 和 `kind=order_cancelled` 都與 Log 一致，`refund_requested=true`，`attempt=0`。
4. **無關事件**：Log 第 4 行是另一張訂單 `r2-shipped-01`，結果 `rejected_shipped`，沒有通知 ID。它與本單無關，我沒有混進來。
5. **設計文件**：`design/design-review.md` 說明正常分支在 HTTP 回應前入列。Worker 送達與 HTTP 回應沒有固定先後，所以 `notify_sent` 的時間不能當作順序證據。文件也註明本輪未跑 .NET，單元、HTTP、payload 和順序重送測試都還是待執行的設計。

## 目前能下的判斷
- 資料上的三方內容互相吻合，但這只是初步觀察。
- `notify_sent` 不自動等於接收端已核對。收據雖然存在，但證據沒有經過固定的 ref 機制，所以我不寫成 confirmed。
- `out/result.json` 兩個狀態都填 `unknown`，`evidence_refs` 留空。

## 未知與缺件
- `collect.py` 未執行，因此沒有合法 ref。
- `gate.py` 未執行，沒有通過紀錄。
- `src/Program.cs` 和 `src/Cancellation.cs` 沒有對照設計文件的行號。文件行號可能過期，需要以當時版本的程式核對。
- 設計文件第 2 點指出，FakeSink 沒存某欄位不代表 payload 沒變。接收端還需要用應用測試觀察 payload。

## 下一步（我沒有做）
1. 核准 `collect.py` 與 `gate.py` 的執行，或由有權限的人跑。
2. 依輸出的 `records[].ref` 把證據補進 `result.json`。如果 ref 對得上，`sender_status` 和 `receiver_status` 很可能可以改成 confirmed。
3. 核對 `src/` 的兩個檔案。

我沒有補送、恢復資料或結案。`out/result.json` 是唯一寫入的檔案，沒有改動 task.json、data/ 或 scripts/。