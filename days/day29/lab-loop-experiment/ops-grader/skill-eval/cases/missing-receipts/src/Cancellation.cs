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

        // 尚未出貨的訂單可以取消，回傳 Cancelled=true（specs/rules-v2.md BR-01）
        // 已付款、尚未出貨、尚未取消時，取消要提出退款要求（specs/rules-v2.md BR-03，Owner 推翻 v1 第3列決定）
        // 已取消的訂單再次取消：維持原狀、不重複提出退款要求（specs/rules-v2.md BR-04）
        var refundRequested = order.Paid && !order.Cancelled;
        var cancelledOrder = order with { Cancelled = true };
        return new CancellationResult(cancelledOrder, refundRequested);
    }

    /// 這次呼叫有沒有真的把狀態從未取消改成已取消（通知的分母；非業務規則）。
    public static bool Transitioned(Order before, CancellationResult after) => !before.Cancelled && after.Order.Cancelled;
}
