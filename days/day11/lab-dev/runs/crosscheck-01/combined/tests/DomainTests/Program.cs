using OrderCancel.Domain;

// specs/rules-v2.md SC-01~07；exit code = 失敗數。
int failures = 0;
void Check(string sc, string name, Func<bool> f)
{
    bool ok; try { ok = f(); } catch (Exception e) { ok = false; name += $" (threw {e.GetType().Name})"; }
    Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {sc} {name}");
    if (!ok) failures++;
}

// SC-01｜BR-01：未出貨、未付款、未取消 → Cancelled=true、RefundRequested=false
Check("SC-01", "尚未出貨、未付款可取消且不要求退款", () =>
{
    var r = Cancellation.Cancel(new Order(Shipped: false, Paid: false, Cancelled: false));
    return r.Order.Cancelled && !r.Order.Shipped && !r.RefundRequested;
});

// SC-02｜BR-02：已出貨、未取消 → 回傳原訂單、不丟例外
Check("SC-02", "已出貨不可取消，回傳原訂單且不要求退款", () =>
{
    var o = new Order(Shipped: true, Paid: false, Cancelled: false);
    var r = Cancellation.Cancel(o);
    return r.Order == o && !r.RefundRequested;
});

// SC-03｜BR-03：已付款、未出貨、未取消 → Cancelled=true、RefundRequested=true
Check("SC-03", "已付款取消要求退款", () =>
{
    var r = Cancellation.Cancel(new Order(Shipped: false, Paid: true, Cancelled: false));
    return r.Order.Cancelled && r.RefundRequested;
});

// SC-04｜BR-03：未付款、未出貨、未取消 → RefundRequested=false
Check("SC-04", "未付款取消不要求退款", () =>
{
    var r = Cancellation.Cancel(new Order(Shipped: false, Paid: false, Cancelled: false));
    return r.Order.Cancelled && !r.RefundRequested;
});

// SC-05｜BR-02：已出貨、已付款 → 回傳原訂單、RefundRequested=false
Check("SC-05", "已出貨已付款仍不可取消也不要求退款", () =>
{
    var o = new Order(Shipped: true, Paid: true, Cancelled: false);
    var r = Cancellation.Cancel(o);
    return r.Order == o && !r.RefundRequested;
});

// SC-06｜BR-04：未出貨、已取消、未付款 → 回傳原訂單、RefundRequested=false、不丟例外
Check("SC-06", "已取消訂單再次取消維持原狀（未付款）", () =>
{
    var o = new Order(Shipped: false, Paid: false, Cancelled: true);
    var r = Cancellation.Cancel(o);
    return r.Order == o && !r.RefundRequested;
});

// SC-07｜BR-04：未出貨、已取消、已付款 → 回傳原訂單、RefundRequested=false（不重複退款）
Check("SC-07", "已取消訂單再次取消不重複提出退款（已付款）", () =>
{
    var o = new Order(Shipped: false, Paid: true, Cancelled: true);
    var r = Cancellation.Cancel(o);
    return r.Order == o && !r.RefundRequested;
});

Console.WriteLine(failures == 0 ? "PASS: 全部條件通過" : $"FAIL: {failures} 項條件未通過");
return failures;
