namespace OrderCancel.Domain;

public record Order(bool Shipped, bool Paid, bool Cancelled);
public record CancellationResult(Order Order, bool RefundRequested);

public static class Cancellation
{
    public static CancellationResult Cancel(Order order)
    {
        // 已出貨的訂單不可取消：維持原訂單，Cancelled 不變，不丟例外（decisions.md 第2列）
        if (order.Shipped)
        {
            return new CancellationResult(order, RefundRequested: false);
        }

        // 已取消的訂單再次取消不重複處理（BR-04）
        if (order.Cancelled)
        {
            return new CancellationResult(order, RefundRequested: false);
        }

        // 尚未出貨、尚未取消的訂單可以取消，回傳 Cancelled=true
        // 已付款的訂單取消時提出退款要求（spec v2 BR-03）
        // 未付款的訂單取消時不提出退款要求（BR-01）
        var refundRequested = order.Paid;
        var cancelledOrder = order with { Cancelled = true };
        return new CancellationResult(cancelledOrder, RefundRequested: refundRequested);
    }

    /// 這次呼叫有沒有真的把狀態從未取消改成已取消（通知的分母；非業務規則）。
    public static bool Transitioned(Order before, CancellationResult after) => !before.Cancelled && after.Order.Cancelled;
}
