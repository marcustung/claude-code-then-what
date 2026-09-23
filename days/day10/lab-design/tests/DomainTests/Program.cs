using OrderCancel.Domain;

// v1 三個測試（沿 Day 6 教學示範）；exit code = 失敗數。
int failures = 0;
void Check(string sc, string name, Func<bool> f)
{
    bool ok; try { ok = f(); } catch (Exception e) { ok = false; name += $" (threw {e.GetType().Name})"; }
    Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {sc} {name}");
    if (!ok) failures++;
}
Check("v1-1", "尚未出貨可取消", () => Cancellation.Cancel(new Order(false, false, false)).Order.Cancelled);
Check("v1-2", "已出貨不可取消", () => { var o = new Order(true, false, false); return Cancellation.Cancel(o).Order == o; });
Check("v1-3", "已付款取消不要求退款", () => { var r = Cancellation.Cancel(new Order(false, true, false)); return r.Order.Cancelled && !r.RefundRequested; });
Console.WriteLine(failures == 0 ? "PASS: 全部條件通過" : $"FAIL: {failures} 項條件未通過");
return failures;
