# spec.md（合成教學案例，非公司系統）

## 需求（工單 ORD-142，v1，全部內容）
讓使用者可以取消尚未出貨的訂單。

## 現有程式骨架（不可改簽名）
```csharp
public record Order(bool Shipped, bool Paid, bool Cancelled);
public record CancellationResult(Order Order, bool RefundRequested);
public static class Cancellation { public static CancellationResult Cancel(Order order) => throw new System.NotImplementedException(); }
```

## 執行限制
不連付款服務、不執行退款、無網路與檔案副作用；RefundRequested 只是記憶體旗標。
