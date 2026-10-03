## 查核結果（r2-healthy-01）

**固定檢查未執行。** 本工作階段沒有 Bash 或 Python,所以我沒跑 `collect.py` 和 `gate.py`。我也不能說已通過。`evidence_refs` 是我照 `collect.py` 的邏輯手動推得,不是它產生的。結果停在「交人核對」,不能自稱 READY_FOR_REVIEW。

**範圍**
- 訂單是 `r2-healthy-01`,版本是 `delivery-hardening-local-r2`。
- 環境是本機教學 fixture,不是正式環境。
- 沒有連 Log server,只用 `data/`、`src/`、`design/`。

**1. 程式與設計(版本與流程)**
- `src/Program.cs:49-94`:取消成功並狀態轉換後,才建立通知(`:82`)並入列(`:88`)。
- `src/Program.cs:225-261`:背景 worker 取出通知後 POST 到 sink。送出成功才記 `notify_sent`。
- `design/design-review.md` 第 1 點說,API 回應與 worker 送達沒有固定先後。所以 `notify_sent` 只代表發送端觀察。
- 日誌的 `version` 與 task.json 一致。

**2. 通知 ID**
- 查詢條件:`data/logs.jsonl` 中 `order_id = r2-healthy-01`。
- 取消事件在 `data/logs.jsonl:2`,通知 ID 為 `7e746d20853d48b9b3948c1fe92319c1`。

**3. 三方分開**
- **API 結果**(`logs.jsonl:2`):`result=ok`、`transitioned=true`、`refund_requested=true`,HTTP 200。
- **發送端**(`logs.jsonl:3`,ref `log:3`):`notify_sent`,通知 ID、訂單 ID 和版本都相符。**sender = confirmed。**
- **接收端**(`data/receipts.json` 第 0 筆,ref `receipt:0`):
  - status 200。
  - payload 的 `notification_id`、`order_id`、`kind=order_cancelled`、`refund_requested=true`、`attempt=0` 與發送端一致。
  - 時間 1790646010.858 早於 `notify_sent` 的 .861,順序合理。
  - **receiver = confirmed。**
  - 版本欄位 receipts.json 本身沒有,只能沿用 `notify_sent` 的版本,所以這項是間接依據。

**4. 排除項**
- `logs.jsonl:4` 是另一張訂單 `r2-shipped-01`:`rejected_shipped`、`notification_id=null`,不屬於本次事件,不混入。
- 沒有 `notify_dead_letter`、`notify_deferred` 或 `notify_attempt_failed`,所以沒有重送或失敗的跡象。

**5. 未知與限制**
- receipts.json 是 FakeSink 紀錄。設計文件第 2 點提醒它未保存 `refund_requested` 不等於 payload 未變。這裡有保存,但仍只是本機接收端。
- `task.json` 沒有 `notification_id`,而 `check_result.py` 會讀 `task["notification_id"]`,所以我推測 `gate.py` 可能回 INPUT_ERROR。我沒改 task.json(規定不可改),需要人確認或補欄位。
- 設計文件第 7 點說本輪沒跑 .NET,程式行為是靠讀碼,不是實際執行。

**結論:** 在這個本機 fixture 內,發送端和接收端都有對得上的紀錄。但固定檢查沒跑,且 task.json 缺 `notification_id`,所以結果只能交人核對,不算通過。

**下一步(最小補查)**
- 在有 Python 的環境依序跑 `collect.py .` 和 `gate.py .`。
- 比對 `records[].ref` 是否確實是 `log:3` 和 `receipt:0`。
- 由有權限的人決定 task.json 缺 `notification_id` 怎麼處理。

我沒有補送、核准或結案。結果已寫入 `out/result.json`。