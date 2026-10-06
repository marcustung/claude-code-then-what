using OrderCancel.Domain;

// specs/rules-v2.md 的 SC-01～SC-07，一格一個 Check；exit code = 失敗數。與 Day 6／10 相同的 console 判準風格。
int failures = 0;
void Check(string sc, string name, Func<bool> f)
{
    bool ok; try { ok = f(); } catch (Exception e) { ok = false; name += $" (threw {e.GetType().Name})"; }
    Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {sc} {name}");
    if (!ok) failures++;
}
CancellationResult C(bool shipped, bool paid, bool cancelled) => Cancellation.Cancel(new Order(shipped, paid, cancelled));

Check("SC-01", "未出貨未付款可取消，Cancelled=true、Refund=false", () => { var r = C(false, false, false); return r.Order.Cancelled && !r.RefundRequested; });
Check("SC-02", "已出貨：回原訂單、不丟例外", () => { var o = new Order(true, false, false); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
Check("SC-03", "已付款未出貨取消 → RefundRequested=true（v2 BR-03，反轉 v1）", () => { var r = C(false, true, false); return r.Order.Cancelled && r.RefundRequested; });
Check("SC-04", "未付款取消 → RefundRequested=false", () => !C(false, false, false).RefundRequested);
Check("SC-05", "已出貨已付款：原訂單、Refund=false", () => { var o = new Order(true, true, false); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
Check("SC-06", "已取消再取消（未付款）：原狀、Refund=false、不丟例外", () => { var o = new Order(false, false, true); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
Check("SC-07", "已取消再取消（已付款）：原狀、Refund=false（不重複退款）", () => { var o = new Order(false, true, true); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
Check("NC-01", "Transitioned 只在 false→true 為真", () => { var o = new Order(false, true, false); var r = Cancellation.Cancel(o); return Cancellation.Transitioned(o, r); });
Check("NC-02", "重複取消 Transitioned=false", () => { var o = new Order(false, true, true); var r = Cancellation.Cancel(o); return !Cancellation.Transitioned(o, r); });

Console.WriteLine(failures == 0 ? "PASS: 全部條件通過" : $"FAIL: {failures} 項條件未通過");
return failures;
