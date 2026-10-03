## 查核結果：固定檢查未執行，結論停在待查

**範圍**
- 訂單：`r2-healthy-01`
- 版本：`delivery-hardening-local-r2`
- 環境：本機教學 fixture，不是正式環境（來源：`task.json`）
- 未連 Log server，也沒有補送或結案。

**卡點**
- 我嘗試了兩次執行 `collect.py`，兩次都需要核准，沒有被放行。
- 因此沒有 `records[].ref` 可以引用，`gate.py` 也沒跑。
- 我沒有自編 ref，也沒有改動 task.json、data/ 或 scripts/。

**人工閱讀所得（未經檢查器驗證）**

1. **程式與設計**
   - `src/Program.cs:79-88`：取消成功（transitioned）時建立通知並寫入 channel。
   - `src/Program.cs:92`：寫 `cancel` 日誌，內含 notification_id。
   - `src/Program.cs:257-261`：worker 收到接收端成功回應後，才寫 `notify_sent`。
   - `design/design-review.md:3,9`：Worker 的送達與 HTTP 回應沒有固定先後；本輪未跑 .NET。

2. **API 結果**
   - `data/logs.jsonl:2`：取消結果 `ok`，transitioned 為 true，refund_requested 為 true。
   - 通知 ID 是 `7e746d20853d48b9b3948c1fe92319c1`。

3. **發送端觀察**
   - `data/logs.jsonl:3`：同一個 notification_id 有 `notify_sent`，版本與 task 相符。
   - 沒有 `notify_attempt_failed`、`notify_deferred`、`dead_letter`。
   - `logs.jsonl:1` 顯示 `faults_loaded` 為 false，沒有注入故障。

4. **接收端佐證**
   - `data/receipts.json` item 0：status 200。
   - payload 的 notification_id、order_id、request_id、kind 和 `refund_requested: true` 都與日誌一致，`attempt` 為 0。
   - `at` 為 1790646010.857，換算約 09:40:10.857（+08:00），早於 notify_sent 的 10.861。這符合先收到、再記 sent 的順序。

5. **其他訂單**
   - `logs.jsonl:4` 是 `r2-shipped-01` 被拒（rejected_shipped），沒有通知，屬於不同事件，不混入。
   - 這一行的 `request_id` 與 `run_id` 沿用 healthy 那筆，可能是演練標頭重用，我沒有據此下結論。

**我的判斷**
- 人工看來，發送端和接收端證據都一致，這筆通知看起來正常送達。
- 依 Skill 規則，這個判斷沒有檢查器驗證，所以我不寫成 confirmed。
- `receipts.json` 本身沒有版本欄位，接收端版本只能沿用 `notify_sent` 的版本，這點檢查器也會標註。

**未知與缺件**
- `collect.py` 和 `gate.py` 的輸出。
- 只有單一收據，沒有其他接收端來源可交叉核對。
- 設計文件的行號可能已過期。我讀的 `Program.cs` 是目前本機版本，行號以它為準，部署版本是否同一份無法確認。

**輸出檔**
- 已寫 `out/result.json`：`sender_status` 和 `receiver_status` 都填 `unknown`，`evidence_refs` 為空，`next_action` 說明待檢查器。
- 這是保守填法，會低估人工閱讀的結果。

**下一步（需要你決定）**
- 授權我執行：
  - `python …/scripts/collect.py .`
  - `python …/scripts/gate.py .`
- 預期 `evidence_refs` 會是 `log:3` 和 `receipt:0`，但這只是我讀 collect.py 邏輯的推測，要以實際輸出為準。
- 授權後我會更新 result.json，把兩端改成 confirmed（若檢查通過），並依 gate 結果再修正最多一次。