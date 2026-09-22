## 規劃（先不改碼）

**要改的檔案：`src\Domain\Cancellation.cs`**

- 第 16–21 行的邏輯要改：
  - 新增判斷：若訂單**已經是 `Cancelled == true`**，直接回傳原 `order`、`RefundRequested: false`（不可重複提出退款）。
  - 未取消、未出貨的情況下取消時，`RefundRequested` 改成 `order.Paid`（已付款才要求退款，未付款則不要求）。
- 同步更新第 16–19 行的註解，移除「已付款不提出退款」「待確認」等舊敘述，改為說明新規則（已付款→退款、已取消→不可重複退款）。

**要改的檔案：`tests\DomainTests\Program.cs`**

- 第 13 行（`v1-3`）：情境敘述與斷言要改成「已付款取消**要**提出退款」，即 `r.RefundRequested` 應為 `true`。
- 新增測試 `v1-4`：同一張已付款、已取消的訂單再取消一次 →
  - `RefundRequested == false`
  - `Order` 維持不變（不應重複觸發退款）
- 可選新增測試：未付款訂單取消 → `RefundRequested == false`（回歸驗證，避免改動誤觸發退款）。

需要我接著實作這些修改嗎？