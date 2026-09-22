# 開工前分析：訂單取消規則 v1→v2（依 rules-v2.md）

## 1. 現有程式與測試現況（程式事實，附行號）

**`src/Domain/Cancellation.cs`**
- `Order` 為 record，含 `Shipped`、`Paid`、`Cancelled` 三個 bool（Cancellation.cs:3）。`CancellationResult` 含 `Order`、`RefundRequested`（Cancellation.cs:4）。
- `Cancel(order)` 邏輯（Cancellation.cs:8-22）：
  - 若 `Shipped == true`：直接回傳原 `order`，`RefundRequested=false`（Cancellation.cs:11-14）。
  - 否則（不論 `Paid`、也不論是否已 `Cancelled`）：一律回傳 `order with { Cancelled = true }`，`RefundRequested=false`（Cancellation.cs:20-21）。
  - **程式事實**：目前完全沒有讀取 `order.Cancelled` 來分支；`Paid` 欄位存在但從未被讀取使用於任何判斷。
- `Transitioned(before, after)`（Cancellation.cs:25）：純比較 before/after 是否從未取消變已取消，程式碼註解自述「非業務規則」，目前無任何呼叫方使用它。
- 程式碼註解（Cancellation.cs:18-19）已明白標註「已取消再取消」屬未確認行為，不應據此寫測試預期——這是 v1 時期的自我警示，而非已驗證的行為。

**`tests/DomainTests/Program.cs`**
- 共 3 個測試（v1-1、v1-2、v1-3），對應 decisions-v1.md 已確認的 3 條（Program.cs:11-13）：
  - v1-1：未出貨可取消 → `Cancelled=true`。
  - v1-2：已出貨不可取消 → 回傳同一個 `Order` 值。
  - v1-3：已付款取消 → `Cancelled=true` 且 `RefundRequested=false`。
- 沒有涵蓋：已出貨+已付款、已取消再取消（含已付款/未付款）等組合。

## 2. 本次需求（rules-v2.md）相對現況

**不變（v1 保留，rules-v2.md 明示）**
- BR-01 未出貨可取消 → `Cancelled=true`（rules-v2.md:9，對應 SC-01）。
- BR-02 已出貨不可取消，維持原訂單、不丟例外（rules-v2.md:10，對應 SC-02、SC-05）。
- 三型別簽名不可改；不連付款/退款服務（rules-v2.md:13）。

**要改（rules-v2.md 明確標「改」「新」）**
- BR-03（改）：已付款且未出貨取消時，`RefundRequested` 應變為 `true`；未付款則仍為 `false`（rules-v2.md:11）。文件本身寫明「既有測試『已付款取消不要求退款』預期要反過來」——這是**規格要求**，不是我的推論。
  - 程式事實：目前程式無條件回傳 `RefundRequested=false`，不讀 `Paid`，需改動 Cancellation.cs:21 附近邏輯。
- BR-04（新）：已取消訂單再次取消，維持原狀、`RefundRequested=false`、不丟例外（rules-v2.md:12），對應 SC-06、SC-07。
  - 程式事實：目前程式碰到已取消訂單並不會走特殊分支（因為完全不檢查 `Cancelled`），需新增判斷。若只改 BR-03 而不同時處理 BR-04，會導致「已取消+已付款」再取消時被誤判為 `RefundRequested=true`，違反 SC-07（不重複退款）——這是**推論**：兩條規則有交互作用，必須一起改，否則會互相破壞。

**還未確認（超出本票範圍，不可視為已接受）**
- `specs/notification-contract-v2.1.md` 為**另一份提案**，開頭與檔名已自陳「proposed」「作者尚未接受前標提案」（notification-contract-v2.1.md:1, 4）。`decisions-v2.1.md` 所有相關列狀態均為 `proposed`（decisions-v2.1.md:5-12），僅「已出貨取消 409」一列標「沿用」。
- rules-v2.md 第 3 行自稱「v2 由訂單 Owner 於教學示範中確認；本檔是這張票唯一的規則來源」，但**沒有對應的 `decisions-v2.md` 確認紀錄檔可佐證**（相對地 v1 有 `decisions-v1.md`、v2.1 有 `decisions-v2.1.md`）。這一點是**規格自陳**，未見獨立確認紀錄佐證，應視為未知，不宜視同與 v1/v2.1 同等級的已簽核證據。

## 3. 測試預期變更 vs. 缺少的驗收情境

**預期要改**
- v1-3「已付款取消不要求退款」（Program.cs:13）：斷言需反轉為 `RefundRequested=true`（對應 SC-03）。測試名稱也應同步改，否則名實不符。

**缺少、需新增（對應 rules-v2.md 的 SC 表）**
- SC-04：未付款、未出貨、未取消 → `RefundRequested=false`（目前 v1-1 只驗證 `Cancelled=true`，未驗證 `RefundRequested`）。
- SC-05：已出貨、**已付款** → 原訂單、`RefundRequested=false`（v1-2 只測了已出貨+未付款）。
- SC-06：未出貨、已取消、未付款 → 原訂單、`RefundRequested=false`、不丟例外（全新，BR-04）。
- SC-07：未出貨、已取消、**已付款** → 原訂單、`RefundRequested=false`（全新，驗證不重複退款，最能抓出「BR-03/04 交互作用」的迴歸）。

以上四項是**規格已列出**的驗收情境缺口，我只是對照列出，未替未確認需求（如已出貨再取消以外的邊界，或通知相關驗收）杜撰情境。

## 4. 範圍分類：要改 / 不能順手改 / 受阻待問

**要改（本票範圍，rules-v2.md 直接授權）**
- `Cancellation.cs` 的 `Cancel` 方法：加入對 `order.Cancelled` 的分支（BR-04）與對 `order.Paid` 的退款旗標判斷（BR-03）。
- `tests/DomainTests/Program.cs`：修改 v1-3、新增 SC-04/05/06/07 對應測試。

**不能順手改（超出本票，即使技術上方便）**
- 任何 API 層、HTTP 狀態碼（200/409）、`logs.jsonl`、`/metrics`、`receipts.jsonl`、`notification_id`／`request_id`／`run_id`、重試與 `dead_letter` 機制——這些全部只存在於 `notification-contract-v2.1.md`（proposed）與 `decisions-v2.1.md`（proposed），目前程式庫**沒有任何對應實作**，rules-v2.md 也未授權。不可因為 `Transitioned` 函式剛好可當「唯一成功轉換」判斷依據，就順勢接上通知邏輯——那是另一張票。
- 三個型別的簽名（rules-v2.md:13 明文列為 hook 擋點）。

**受阻待問（矛盾／缺口，需人決定，不可自行假設）**
1. **NC-02 與決策記錄互相矛盾**：`notification-contract-v2.1.md` 第16行寫「已取消再取消：API 回 200／ok=false **或 409**（見 API）」；但 `decisions-v2.1.md` 第6列明確決定「200 `{ok:true, transitioned:false}`（冪等成功）**而非** 409」。兩份文件在「重複取消該回 200 還是 409」「ok 該是 true 還是 false」上自相矛盾，且都與本次 rules-v2.md（純 domain，無 HTTP 概念）無關——**但這矛盾本身值得回報**，避免將來直接照抄任一份造成不一致。
2. **通知文件對現況的描述失實**：`notification-contract-v2.1.md` 第8行稱「取消功能通過測試（v1 三綠、v2 七個場景）」，但依程式與測試檔事實，目前只有 v1 三個測試通過；v2 七個 SC 場景尚未寫成測試、更未通過。這句話應視為該提案作者對「未來完成後」的假設性敘述，不能誤讀為現況已達成。
3. **rules-v2.md 的「已由 Owner 確認」缺乏獨立確認紀錄**：與 v1、v2.1 都有對應 decisions 檔案的模式不同，v2 沒有 `decisions-v2.md`。是否要求補一份，或以其他方式留痕，待人決定。
4. **BR-04 與 SC-06/07 的例外處理是否需要顯式測試「不丟例外」**：目前 record 值相等自然滿足「維持原狀」，但這是實作細節巧合還是規格硬性要求（未來若改資料結構會不會破功），值得在設計時明確寫成契約假設。

## 5. 進入設計前，應由人決定的問題 / 可交給設計者的材料

**應由人決定（不可由 AI 代為核准）**
- 是否要在本次改動中，把 `notification-contract-v2.1.md` 一併視為本票範圍？（目前判斷：不應該，因為狀態是 `proposed` 且 rules-v2.md 自稱是「唯一規則來源」，未提及通知）
- `notification-contract-v2.1.md` 與 `decisions-v2.1.md` 對「重複取消回應碼」的矛盾（200 vs. 409），由誰、何時裁定並更新哪一份文件。
- 是否需要為 rules-v2.md 補一份 `decisions-v2.md` 作為 Owner 確認的獨立證據。

**可直接交給設計者的材料**
- rules-v2.md 的 BR-01~04、SC-01~07 表格，可直接作為本次 `Cancellation.cs` 改動與測試新增／修改的依據。
- 現況落差清單：v1-3 測試需反轉；SC-04/05/06/07 缺測試；`Cancel` 方法需新增對 `Cancelled`、`Paid` 的分支邏輯。
- 明確排除清單：本票不含 API、通知、日誌、metrics、重試/dead_letter，這些屬 `notification-contract-v2.1.md`（proposed），待作者接受後另立票。