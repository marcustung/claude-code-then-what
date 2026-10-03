## 查核結果：固定檢查未執行，結論停在待查

**範圍**：order `r2-healthy-01`，版本 `delivery-hardening-local-r2`，來源是本機教學 fixture（task.json），不是正式環境，沒有連 Log server。

### 卡點
- `collect.py` 與 `gate.py` 在執行時都跳出「需要核准」，我沒有取得執行權限。`.claude/settings.json` 雖然有 allow 規則，但命令仍被擋。
- 所以我拿不到 `records[].ref`，`evidence_refs` 只能留空，不自編。
- 固定檢查（gate.py）未執行，不能說已通過。
- Skill 指定的腳本路徑是 `mkt-20261003-232727/plugins/...`，目前專案目錄是 `marketplace-team-20261003-232727`。兩個路徑不同，核准時請確認。

### 已讀到的依據（人工閱讀，非 ref）
1. **程式（src/Program.cs:79-88、:98）**：取消成功（transitioned）才建立通知，再寫入 Channel。非同步模式下，Worker 在 POST 到 sink 回 2xx 後才記 `notify_sent`。
2. **取消事件（data/logs.jsonl 第 2 行）**：
   - 事件內容：`cancel`、`result=ok`、`transitioned=true`、`refund_requested=true`。
   - `notification_id=7e746d20853d48b9b3948c1fe92319c1`。
3. **發送端（logs.jsonl 第 3 行）**：同一個 notification_id 有 `notify_sent`，時間 09:40:10.861。
4. **接收端（data/receipts.json 第 1 筆）**：
   - 同一個 notification_id，status 200，`kind=order_cancelled`，`refund_requested=true`，`attempt=0`。
   - 收據的 `at` 換算約為 09:40:10.858，早於發送端 log 的 .861，符合「先收到、後記 sent」。
5. **旁證**：logs.jsonl 第 4 行是另一張單 `r2-shipped-01`，結果 `rejected_shipped`，沒有 notification_id。這是不同訂單，不併入本事件。
6. **設計（design/design-review.md）**：
   - 第 2 點：收據不保存 `refund_requested` 不等於 payload 未變。
   - 第 7 點：本輪未跑 .NET，新增的測試都是待執行設計。

### 初步判斷（尚未經檢查器核對）
從人工比對看，發送端和接收端的證據彼此吻合，沒有發現矛盾。但這不是固定檢查的結果，所以 `out/result.json` 兩個狀態都保守填 `unknown`，不填 confirmed。

### 未知與限制
- 沒有 .NET 執行紀錄，只確認 fixture 資料與程式讀起來一致，沒有實際重跑。
- logs.jsonl 的 `ts` 帶 +08:00，receipts.json 的 `at` 是 epoch，兩者時間換算是我手算的，尚未驗證。
- 這份 fixture 只有一筆收據，沒有重送或重複通知的資料，無法判斷冪等性。

### 產出
- `out/result.json` 已寫入（契約 v1）：`sender_status=unknown`、`receiver_status=unknown`、`evidence_refs=[]`，`missing_sources` 記下 collect.py 與 gate.py 未執行。

### 下一步（需要你操作）
1. 核准執行 `collect.py .`。
2. 我再依 `records[].ref` 補上 `evidence_refs`，並把 sender/receiver 改成 confirmed。這個改動要有 ref 支撐，改完才有意義。
3. 核准後執行一次 `gate.py .`；退出碼 1 時，依 errors 修正，最多重跑一次。

我沒有補送通知、沒有結案，也沒有改動 task.json、data/、src/ 或 design/。