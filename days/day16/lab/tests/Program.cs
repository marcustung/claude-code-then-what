using System;

class Program
{
    static int Main()
    {
        int failures = 0;

        // 尚未出貨、尚未取消的訂單可以取消，回傳 Cancelled=true（decisions.md 第1列）
        failures += Check("尚未出貨可取消", () =>
        {
            var result = Cancellation.Cancel(new Order(Shipped: false, Paid: false, Cancelled: false));
            return result.Order.Cancelled == true;
        });

        // 已出貨的訂單不可取消：維持原訂單，Cancelled 不變，不丟例外（decisions.md 第2列）
        failures += Check("已出貨不可取消", () =>
        {
            var order = new Order(Shipped: true, Paid: false, Cancelled: false);
            var result = Cancellation.Cancel(order);
            return result.Order == order;
        });

        // 已付款、尚未出貨的訂單取消後，不提出退款要求（decisions.md 第3列）
        failures += Check("已付款取消不要求退款", () =>
        {
            var result = Cancellation.Cancel(new Order(Shipped: false, Paid: true, Cancelled: false));
            return result.Order.Cancelled == true && result.RefundRequested == false;
        });

        // 「已取消的訂單再次取消」尚未確認，列為受阻範圍，不在此撰寫測試預期。

        if (failures == 0)
        {
            Console.WriteLine("PASS: 全部條件通過");
        }
        else
        {
            Console.WriteLine($"FAIL: {failures} 項條件未通過");
        }

        return failures == 0 ? 0 : 1;
    }

    static int Check(string name, Func<bool> assertion)
    {
        bool ok;
        try
        {
            ok = assertion();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"FAIL {name}: 拋出例外 {ex.Message}");
            return 1;
        }

        Console.WriteLine(ok ? $"PASS {name}" : $"FAIL {name}");
        return ok ? 0 : 1;
    }
}
