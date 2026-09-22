using System;

public record Order(bool Shipped, bool Paid, bool Cancelled);
public record CancellationResult(Order Order, bool RefundRequested);

public static class Cancellation
{
    public static CancellationResult Cancel(Order order)
    {
        if (order is null) throw new ArgumentNullException(nameof(order));

        if (order.Shipped)
        {
            return new CancellationResult(order, false);
        }

        if (order.Cancelled)
        {
            return new CancellationResult(order, false);
        }

        var cancelledOrder = order with { Cancelled = true };
        var refundRequested = order.Paid;

        return new CancellationResult(cancelledOrder, refundRequested);
    }
}
