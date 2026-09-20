// 2026-09-19 觀察用：把「已取消、未出貨」的訂單再丟進 Claude 交回的 Cancel()，只印結果，不下 PASS/FAIL。
class Program
{
    static int Main()
    {
        var already = new Order(Shipped: false, Paid: true, Cancelled: true);
        var r = Cancellation.Cancel(already);
        System.Console.WriteLine($"INPUT  Shipped={already.Shipped} Paid={already.Paid} Cancelled={already.Cancelled}");
        System.Console.WriteLine($"OUTPUT Cancelled={r.Order.Cancelled} RefundRequested={r.RefundRequested} threw=false");
        System.Console.WriteLine("OBSERVE: repeated cancel returned a result; no test in impl/ covers this path");
        return 0;
    }
}
