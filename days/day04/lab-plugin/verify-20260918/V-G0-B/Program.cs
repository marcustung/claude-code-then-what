using System;

class Program
{
    static int _failures = 0;

    static void Check(string name, bool condition)
    {
        if (condition)
        {
            Console.WriteLine($"PASS: {name}");
        }
        else
        {
            Console.WriteLine($"FAIL: {name}");
            _failures++;
        }
    }

    static void Main()
    {
        // Unshipped, unpaid order: should cancel, no refund
        {
            var order = new Order(Shipped: false, Paid: false, Cancelled: false);
            var result = Cancellation.Cancel(order);
            Check("Unshipped+unpaid: Cancelled becomes true", result.Order.Cancelled);
            Check("Unshipped+unpaid: no refund requested", !result.RefundRequested);
            Check("Unshipped+unpaid: Shipped unchanged (false)", !result.Order.Shipped);
            Check("Unshipped+unpaid: Paid unchanged (false)", !result.Order.Paid);
        }

        // Unshipped, paid order: should cancel, refund requested
        {
            var order = new Order(Shipped: false, Paid: true, Cancelled: false);
            var result = Cancellation.Cancel(order);
            Check("Unshipped+paid: Cancelled becomes true", result.Order.Cancelled);
            Check("Unshipped+paid: refund requested", result.RefundRequested);
            Check("Unshipped+paid: Paid unchanged (true)", result.Order.Paid);
        }

        // Shipped order: should NOT cancel, no refund, order unchanged
        {
            var order = new Order(Shipped: true, Paid: true, Cancelled: false);
            var result = Cancellation.Cancel(order);
            Check("Shipped: Cancelled remains false", !result.Order.Cancelled);
            Check("Shipped: no refund requested", !result.RefundRequested);
            Check("Shipped: order reference/values unchanged", result.Order == order);
        }

        // Shipped and unpaid order: still should not cancel
        {
            var order = new Order(Shipped: true, Paid: false, Cancelled: false);
            var result = Cancellation.Cancel(order);
            Check("Shipped+unpaid: Cancelled remains false", !result.Order.Cancelled);
            Check("Shipped+unpaid: no refund requested", !result.RefundRequested);
        }

        // Already cancelled, unshipped, paid order: idempotent, no double refund
        {
            var order = new Order(Shipped: false, Paid: true, Cancelled: true);
            var result = Cancellation.Cancel(order);
            Check("Already cancelled: stays cancelled", result.Order.Cancelled);
            Check("Already cancelled: no refund requested (avoid double refund)", !result.RefundRequested);
            Check("Already cancelled: order unchanged", result.Order == order);
        }

        // Already cancelled, unshipped, unpaid order
        {
            var order = new Order(Shipped: false, Paid: false, Cancelled: true);
            var result = Cancellation.Cancel(order);
            Check("Already cancelled+unpaid: stays cancelled", result.Order.Cancelled);
            Check("Already cancelled+unpaid: no refund requested", !result.RefundRequested);
        }

        // Null order should throw
        {
            bool threw = false;
            try
            {
                Cancellation.Cancel(null!);
            }
            catch (ArgumentNullException)
            {
                threw = true;
            }
            Check("Null order throws ArgumentNullException", threw);
        }

        Console.WriteLine();
        if (_failures == 0)
        {
            Console.WriteLine("ALL TESTS PASSED");
            Environment.Exit(0);
        }
        else
        {
            Console.WriteLine($"{_failures} TEST(S) FAILED");
            Environment.Exit(1);
        }
    }
}
