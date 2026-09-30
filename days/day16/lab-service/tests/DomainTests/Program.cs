using OrderCancel.Domain;

// SC-01～07（specs/rules-v2.md ORD-142 v2）；exit code = 失敗數。
int failures = 0;
void Check(string sc, string name, Func<bool> f)
{
    bool ok; try { ok = f(); } catch (Exception e) { ok = false; name += $" (threw {e.GetType().Name})"; }
    Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {sc} {name}");
    if (!ok) failures++;
}
Check("SC-01", "未出貨可取消", () => { var r = Cancellation.Cancel(new Order(false, false, false)); return r.Order.Cancelled && !r.RefundRequested; });
Check("SC-02", "已出貨不可取消", () => { var o = new Order(true, false, false); return Cancellation.Cancel(o).Order == o; });
Check("SC-03", "已付款取消要求退款", () => { var r = Cancellation.Cancel(new Order(false, true, false)); return r.Order.Cancelled && r.RefundRequested; });
Check("SC-04", "未付款取消不要求退款", () => { var r = Cancellation.Cancel(new Order(false, false, false)); return !r.RefundRequested; });
Check("SC-05", "已出貨已付款回傳原訂單不退款", () => { var o = new Order(true, true, false); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
Check("SC-06", "已取消未付款再次取消維持原狀不退款", () => { var o = new Order(false, false, true); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
Check("SC-07", "已取消已付款再次取消不重複退款", () => { var o = new Order(false, true, true); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
Console.WriteLine(failures == 0 ? "PASS: 全部條件通過" : $"FAIL: {failures} 項條件未通過");
return failures;
