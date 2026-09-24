## 讀到的來源
- `plan.md`（全文）
- `specs/rules-v2.md`（全文）
- `design-input/scope-handoff.md`、`design-input/design-review.md`
- `src/Api/Program.cs`、`src/Domain/Cancellation.cs`
- `verify-integration.py`（因為 `src/FakeSink/Program.cs` 找不到，見第 3 點說明）

---

### 1. `RefundRequested` 一路經過哪裡

- **算出**：`src/Domain/Cancellation.cs:19` `refundRequested = order.Paid && !order.Cancelled`，包進 `CancellationResult.RefundRequested`（record 定義於 `Cancellation.cs:4`，第 21 行回傳）。
- **API 拿到**：`src/Api/Program.cs:69` `var result = Cancellation.Cancel(before);`。
- **寫進 HTTP 回應**：`Program.cs:89`，JSON 欄位 `refund_requested = result.RefundRequested`。
- **寫進 log**：`Program.cs:88`，`log.Write(...)` 裡 `refund_requested = result.RefundRequested`（落在 `logs.jsonl`）。
- **包進通知物件**：`Program.cs:79`，`new Notification(..., result.RefundRequested)`（record 定義在 `Program.cs:94`）。
- **送到接收端**：
  - 一般路徑：`channel.Writer.WriteAsync(n)`（`Program.cs:84`）→ `NotificationWorker.ExecuteAsync`（`Program.cs:210-253`），POST body 在 `Program.cs:231`，`refund_requested = n.RefundRequested`。
  - `sync_notify` 演練路徑：`NotificationWorker.SendOnce`（`Program.cs:193-208`），POST body 在 `Program.cs:200`。

**注意**：`src/FakeSink/Program.cs` 這個檔案在專案裡不存在——我用 `Glob` 對整個 repo 搜尋 `**/FakeSink*` 與 `**/*Sink*`，都沒有結果。目前唯一扮演「測試接收端」角色的是 `verify-integration.py:12-17` 內嵌的 Python `http.server` handler（class `Sink`），它把收到的 body `json.loads` 後存進 `received` list。這一點與你題目的前提（有 `src/FakeSink/Program.cs`）不符，我沒有依據可以假裝讀過一份不存在的檔案。

---

### 2. 每個接點該看哪份結果

| 接點 | 該看的具體結果 |
|---|---|
| Domain 算對 | `tests/DomainTests/Program.cs` 的 SC-01～07 斷言（已知全綠） |
| HTTP 回應對 | 每次呼叫 `/orders/{id}/cancel` 回傳 JSON 的 `refund_requested` 欄位；`verify-integration.py:30` 把每筆回應存進 `calls`，最後寫成 `runs/<name>/requests.json`（`verify-integration.py:68`） |
| log 對 | `runs/<name>/logs.jsonl` 裡 `event=="cancel"` 那幾行的 `refund_requested` 欄位（`verify-integration.py:58-60` 已有讀取邏輯） |
| 通知/payload 對 | 測試接收端實際收到的 POST body 裡的 `refund_requested` 欄位；執行時存在 `received`（記憶體 list），落盤在 `runs/<name>/payloads.json`（`verify-integration.py:68`） |

---

### 3. 用現有程式與「FakeSink」驗不驗得出來

- `verify-integration.py` 裡**已經有**對應這四個接點的檢查邏輯：HTTP 回應（`verify-integration.py:46`）、log（`:58-60`）、通知 payload 的 `order_id`/`refund_requested`（`:57`）。這些檢查邏輯存在，但我**沒有執行**它們（依 CLAUDE.md 規則，本次由外層 runner 執行，我不宣稱自己跑過），也沒去讀 `runs/` 下任何 `report.json` 逐一核對現在原始碼狀態下的結果，所以不能說「驗得出來且已通過」，只能說「檢查點已經寫好」。
- **驗不出來的一項**：如果你要驗的是一個「獨立的 `src/FakeSink` 專案」（例如可獨立建置、跟 API 分離的假接收端），這在目前的材料裡**不存在**，驗不出來。目前的接收端邏輯耦合寫死在 `verify-integration.py` 一支腳本裡，不是獨立套件。要驗這件事得先新增一個獨立的 FakeSink 專案/檔案——但這超出 `plan.md` 第 2 條與 CLAUDE.md 「只處理 Domain 與測試、不新增套件」的範圍，所以按現在的規則我不能自己動手做。
- **另一個限制**：`verify-integration.py:57` 只驗 payload 裡的 `order_id` 與 `refund_requested` 兩個欄位，不驗其他通知欄位（如 `notification_id`、`kind`）是否完整保留。`design-review.md:4`「FakeSink 未保存 refund_requested 不等於 payload 未變……單看收據不足」印證了這是既有已知限制，不是我新發現的 bug。

---

### 4. 「依序重送不新增通知」要看哪個欄位

看 **`transitioned`** 欄位，不是 `refund_requested`：
- `Program.cs:70` `bool transitioned = Cancellation.Transitioned(before, result);`
- 只有 `transitioned == true` 時才會建立 `Notification` 並入列（`Program.cs:76-84`）。
- HTTP 回應（`Program.cs:89`）與 log（`Program.cs:88`）都各自回傳/寫入 `transitioned`。

原因：`RefundRequested` 本身不能拿來分辨——依 BR-04（`specs/rules-v2.md:12`），重複取消時 `RefundRequested` 也是 `false`，跟「未付款首次取消」的 `false` 無法區分。必須看 `transitioned`（或 `Program.cs:71-74` 對應的 `outcome`，`ok` vs `idempotent`）才知道這次是不是真的狀態轉換、該不該發通知。

---

**哪些是讀到的、哪些是推論**：第 1、2、4 點的欄位、行號、控制流程（何時建立通知、何時寫 log、何時回應）都是直接從 `src/Api/Program.cs`、`src/Domain/Cancellation.cs` 讀到的事實。「`src/FakeSink/Program.cs` 不存在，目前的接收端是 `verify-integration.py` 內嵌的 `Sink` class」也是讀到的事實（Glob 搜尋結果 + 檔案內容）。屬於推論、依據不足的部分：(a) 我推論 `design-review.md` 提到的「FakeSink」概念上等同於 `verify-integration.py` 的 `Sink` class，但沒有任何檔案明文把兩者劃等號，這是我根據排除法做的推論；(b) 我沒有讀取 `runs/` 下任何 `report.json` 或執行腳本，所以「這些檢查現在跑起來會不會過」我沒有依據可以下結論，只能確認檢查邏輯存在；(c) 「新增獨立 FakeSink 專案會違反 CLAUDE.md 範圍限制」是我對規則的解讀推論，不是程式本身的事實。