# ORD-142 v2｜讓使用者可以取消尚未出貨的訂單（2026-09-16 補充退款規則）

需求全文（v1）：Let users cancel orders that have not shipped yet.

v2 補充（訂單 Owner @order-owners，2026-09-16）：
- R-02：已出貨訂單不可取消；呼叫端以 `Order.Cancelled` 未改變判斷未成功，不丟例外。
- R-05：重複取消為冪等，不重複建立退款申請。
- R-07：已付款且未出貨的訂單被取消時，系統建立退款申請（`RefundRequested=true`），實際退款由付款服務處理；未付款訂單不建立退款申請。部分付款不在本工單範圍。

既有介面（不可改簽名）：
- `record Order(bool Shipped, bool Paid, bool Cancelled)`
- `record CancellationResult(Order Order, bool RefundRequested)`
- `Cancellation.Cancel(Order) -> CancellationResult`
