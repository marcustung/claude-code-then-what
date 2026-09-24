namespace OrderCancel.Domain;

public record Order(bool Shipped, bool Paid, bool Cancelled);
public record CancellationResult(Order Order, bool RefundRequested);

public static class Cancellation
{
    public static CancellationResult Cancel(Order order)
    {
        // BR-02: Already shipped orders cannot be cancelled
        if (order.Shipped)
        {
            return new CancellationResult(order, RefundRequested: false);
        }

        // BR-04: Already cancelled orders stay unchanged
        if (order.Cancelled)
        {
            return new CancellationResult(order, RefundRequested: false);
        }

        // BR-01: Not shipped, not yet cancelled → can cancel
        // BR-03: If paid, request refund; if not paid, no refund request
        var cancelledOrder = order with { Cancelled = true };
        return new CancellationResult(cancelledOrder, RefundRequested: order.Paid);
    }

    /// This call triggered a state transition from not-cancelled to cancelled (notification denominator; not a business rule).
    public static bool Transitioned(Order before, CancellationResult after) => !before.Cancelled && after.Order.Cancelled;
}
