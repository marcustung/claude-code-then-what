namespace OrderCancel.Domain;

// 三個型別簽名沿 Day 6 v1，不可改（specs/rules-v1.md）。
public record Order(bool Shipped, bool Paid, bool Cancelled);
public record CancellationResult(Order Order, bool RefundRequested);

public static class Cancellation
{
    // specs/rules-v2.md：BR-01 未出貨未取消可取消；BR-02 已出貨維持原訂單不丟例外；
    // BR-03（v2 改）已付款未出貨取消 → RefundRequested=true；BR-04（v2 新）已取消再取消 → 原狀、false、不丟例外。
    public static CancellationResult Cancel(Order order)
    {
        if (order.Shipped) return new CancellationResult(order, RefundRequested: false);   // BR-02
        if (order.Cancelled) return new CancellationResult(order, RefundRequested: false); // BR-04
        var cancelled = order with { Cancelled = true };                                    // BR-01
        return new CancellationResult(cancelled, RefundRequested: order.Paid);              // BR-03
    }

    /// 這次呼叫有沒有真的把狀態從未取消改成已取消（通知契約 NC-01 的分母）。
    public static bool Transitioned(Order before, CancellationResult after) => !before.Cancelled && after.Order.Cancelled;
}
