## 查核結果:待查(NEEDS_FOLLOWUP),固定檢查未執行

**範圍**:訂單 `r2-healthy-01`,版本 `delivery-hardening-local-r2`。環境是本機教學 fixture,不是正式環境(來源:`task.json`)。沒有連 Log server,只用本機檔案。

### 卡點
`.claude/skills/trace-notification/` 底下只有 `SKILL.md`,`scripts/collect.py` 和 `scripts/gate.py` 都不存在。

- 我跑不出 `records[].ref`,所以 `evidence_refs` 只能留空。我沒有自編 ref。
- 固定檢查沒有執行,所以這份結果不能說已通過。我也沒有修改或補寫任何腳本和資料。

### 依據
1. **程式與設計**
   - `src/Program.cs:82-84`:取消成功時建立通知並入列,`notify_enqueued_total` 加一。
   - `src/Program.cs:92`:`cancel` 日誌帶 `notification_id`。
   - `src/Program.cs:246`:Worker 送出的 payload 含 `refund_requested`。
   - `src/Program.cs:37`:`/version` 回報 `notification_mode` 為 async,`storage` 為 in-memory。
   - `design/design-review.md` 第 1 點:Worker 送達與 HTTP 回應沒有固定先後。
   - `design/design-review.md` 第 7 點:本輪沒跑 .NET,新增測試只是待執行的設計。
2. **發送端觀察**(`data/logs.jsonl`)
   - 第 2 行:`cancel` 結果 ok,`transitioned=true`,`refund_requested=true`,通知 ID 為 `7e746d20…c1`。
   - 第 3 行:同一個通知 ID 有 `notify_sent`。
   - 這只是服務自己的紀錄,不等於接收端已核對。
3. **接收端佐證**(`data/receipts.json`)
   - 有 1 筆收據:通知 ID 相同,`status` 200,`order_id` 相同,`refund_requested` 為 true,`attempt` 為 0。
   - 這筆收據看起來和發送端吻合。但依 Skill,`confirmed` 必須有 collect 產生的 ref 支撐,我目前沒有,所以不能填。
   - 設計文件第 2 點也提醒,單看收據不足以證明 payload 沒被改過。
4. **日誌裡的另一筆**
   - 第 4 行是 `r2-shipped-01`,結果 `rejected_shipped`,沒有通知 ID。
   - 這是不同訂單,依規則不通知,所以沒有混進本次查核。
   - 這筆的 `request_id` 與 `run_id` 沿用 `r2-healthy-…`,我只把它列為觀察,沒有據此推論。

### 輸出狀態
`out/result.json` 已寫入:

| 欄位 | 值 |
|---|---|
| `sender_status` | unknown |
| `receiver_status` | unknown |
| `evidence_refs` | 空 |
| `missing_sources` | collect.py、gate.py、records[].ref |

兩個狀態填 unknown 是因為缺 ref,不是因為資料顯示沒送達。依上面的觀察,實際看起來已送出並收到,只是沒有可引用的 ref。

### Unknown 與下一步
- **缺的來源**:兩支腳本。請補上,或告訴我它們在哪裡。
- **補齊後的做法**:
  1. 重跑 `collect.py`,取得 `log:N` 和 `receipt:0` 的 ref。
  2. 把兩個狀態更新到有 ref 支撐的程度,再執行 `gate.py`。
  3. 若退出碼為 1,依 `errors` 修正,最多再跑一次。
- **還沒驗證的事**:
  - 本輪沒跑 .NET,payload 內容沒有端到端驗證。
  - 只看到單次嘗試,沒有重送或順序的資料。
- 我沒有補送通知,也沒有結案。