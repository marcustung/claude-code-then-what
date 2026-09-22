讀完 spec.md、`Cancellation.cs`、`Program.cs`、`tests/DomainTests/Program.cs`後，整理如下（未做任何修改，僅盤點）。

## 需求對照現況

spec.md 明確寫：「已付款取消時提出退款要求」。但 `src/Domain/Cancellation.cs:21` 目前寫死 `RefundRequested: false`，且第 16-19 行的注解還宣稱「已付款、尚未出貨的訂單取消後，不提出退款要求」——這與 spec 直接矛盾。這是本次唯一需要改的邏輯點。

## 建議修改

**1. `src/Domain/Cancellation.cs`**
- 第 17 行：刪除/改寫「已付款、尚未出貨的訂單取消後，不提出退款要求（decisions.md 第3列）」這行注解。
  - 注意：`decisions.md` 在此 repo 中不存在（我用 Glob 確認過），現有多處注解引用它（第 10、16、18 行），屬於失效引用，交接時建議提醒 RD 一併確認來源文件是否遺失或本來就不該引用。
- 第 21 行：
  ```csharp
  return new CancellationResult(cancelledOrder, RefundRequested: false);
  ```
  改為
  ```csharp
  return new CancellationResult(cancelledOrder, RefundRequested: order.Paid);
  ```
- 第 18-19 行「已取消訂單再次取消」的待確認注解可保留，因為 spec.md 第 6 行明確列為未決事項，不在本次範圍。

**2. `src/Api/Program.cs`**
- 不需要改。`refund_requested` 欄位（第 89 行、log 第 88 行）都是直接透傳 `Cancellation.Cancel` 的結果，邏輯已經正確接住 Domain 層的改動，不用動。

**3. `tests/DomainTests/Program.cs`**
- 第 13 行 `v1-3` 目前斷言「已付款取消**不**要求退款」，與新需求相反，必須改掉：
  ```csharp
  Check("v1-3", "已付款取消要求退款", () => { var r = Cancellation.Cancel(new Order(false, true, false)); return r.Order.Cancelled && r.RefundRequested; });
  ```
- 建議新增一筆測試，鎖住「未付款取消不應要求退款」，避免以後又退化回全部回 true 或全部回 false：
  ```csharp
  Check("v1-4", "未付款取消不要求退款", () => { var r = Cancellation.Cancel(new Order(false, false, false)); return r.Order.Cancelled && !r.RefundRequested; });
  ```
- 第 12 行 `v1-2`（已出貨不可取消）不受影響，不用動。

## 提醒 RD 的邊界事項（本次不處理，但值得留意）
- 重複取消已付款訂單：目前 `Cancel` 不檢查 `order.Cancelled`，重複呼叫仍會算出 `RefundRequested: order.Paid`；而 `Program.cs:89` 的 API 回應不論 `transitioned` 與否都直接回傳 `result.RefundRequested`。也就是說改完後，**重複取消一筆已付款訂單，API 仍會回 `refund_requested: true`，即使沒有真的轉態、也不會觸發通知**。spec.md 第 6 行把「重複取消應回傳什麼」列為未決，所以這次不用修，但建議在 PR 描述或交接紀錄裡點出來，避免下游誤以為每次收到 `refund_requested: true` 都代表有新的退款事件發生。