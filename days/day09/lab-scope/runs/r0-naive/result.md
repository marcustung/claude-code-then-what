已有 `specs/rules-v2.md` 明確定義這次需求（BR-03 改、BR-04 新），規劃如下：

## 1. `src/Domain/Cancellation.cs`

- **第 11-14 行（已出貨分支）**：不變。
- **第 16-21 行（未出貨分支）**：改成依 `Cancelled` 狀態分流：
  - 若 `order.Cancelled == true`（BR-04，已取消再取消）：原樣回傳 `order`、`RefundRequested=false`，不丟例外。
  - 若 `order.Cancelled == false`（BR-01/BR-03）：`Cancelled=true`，`RefundRequested = order.Paid`（已付款 → `true`，未付款 → `false`）。
- 順帶把第 10、16-19 行的舊註解（提到「不提出退款要求」「待確認」）更新，避免誤導。

## 2. `tests/DomainTests/Program.cs`

- **第 13 行**：既有測試「已付款取消不要求退款」的預期要反過來，改成「已付款取消要提出退款」（對應 SC-03），斷言 `RefundRequested == true`。
- **新增測試**（對應 SC-04～SC-07）：
  - SC-04：未付款、未出貨、未取消 → `RefundRequested=false`
  - SC-05：已出貨、已付款 → 回傳原訂單、`RefundRequested=false`
  - SC-06：未出貨、已取消、未付款 → 原訂單、`RefundRequested=false`、不丟例外
  - SC-07：未出貨、已取消、已付款（重複取消不重複退款）→ 原訂單、`RefundRequested=false`

這樣可完整涵蓋 rules-v2.md 的 SC-01～SC-07。要我接著動手改嗎？