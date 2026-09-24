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

        // 尚未出貨、尚未取消的訂單可以取消，回傳 Cancelled=true（spec.md ORD-142 v1；decisions.md 第1列）
        // 已付款、尚未出貨的訂單取消後，不提出退款要求（decisions.md 第3列）
        // 注意：已取消的訂單再次取消屬於未確認行為（decisions.md 第5列，待確認），
        // 此處僅為滿足簽名而回傳同樣結果，不代表已驗證或已確認的行為，不應據此撰寫測試預期。
        var cancelledOrder = order with { Cancelled = true };
        return new CancellationResult(cancelledOrder, RefundRequested: false);
    }

    /// 這次呼叫有沒有真的把狀態從未取消改成已取消（通知的分母；非業務規則）。
    public static bool Transitioned(Order before, CancellationResult after) => !before.Cancelled && after.Order.Cancelled;
}
