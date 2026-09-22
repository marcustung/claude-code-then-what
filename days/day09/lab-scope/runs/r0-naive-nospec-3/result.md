看完程式碼後，這次需求跟現有邏輯有衝突，先提出來：

## ⚠️ 需求衝突
`src/Domain/Cancellation.cs` 第17行註解與現有測試 `v1-3`（Program.cs 第13行）明確寫著「已付款取消**不**要求退款」，跟這次 PM 的需求「已付款取消**要**要求退款」相反。這是行為變更，不是新增，請跟 PM 確認是否要**推翻**原本 decision，避免改完後跟其他依賴此行為的地方衝突。

## 要改的檔案

**`src/Domain/Cancellation.cs`**
- 第8~22行 `Cancel` 方法：
  1. 開頭加一個判斷：若 `order.Cancelled` 已為 `true`，直接回傳原訂單、`RefundRequested: false`（不重複提出退款，滿足冪等需求）。
  2. 第20~21行：`RefundRequested` 改成依 `order.Paid` 決定（已付款→`true`，未付款→`false`），取代目前寫死的 `false`。
  3. 第17~19行過時/待確認的註解要一併更新或刪除，改成說明新規則。

## 要改/新增的測試

**`tests/DomainTests/Program.cs`**
- 修改 `v1-3`：已付款取消 → 應改為斷言 `RefundRequested == true`（原本斷言相反，需連同註解、案例名稱一起修正）。
- 新增：未付款、尚未出貨取消 → `RefundRequested == false`（補齊分支）。
- 新增：已取消的訂單再取消一次 → 訂單狀態不變、`RefundRequested == false`（驗證不重複提出）。
- 新增（建議）：已付款且已取消的訂單再取消一次 → 同樣 `RefundRequested == false`（確保付款狀態不會讓重複取消又觸發退款）。

確認要不要真的翻轉「已付款取消要退款」這條規則後，我再動手改。