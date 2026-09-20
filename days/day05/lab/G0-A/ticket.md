# ORD-142｜讓使用者可以取消尚未出貨的訂單

需求全文：Let users cancel orders that have not shipped yet.

既有介面（不可改簽名）：
- `record Order(bool Shipped, bool Paid, bool Cancelled)`
- `record CancellationResult(Order Order, bool RefundRequested)`
- `Cancellation.Cancel(Order) -> CancellationResult`
