看完程式碼,注意到目前 `Cancel` 方法對「已付款取消」的行為與新需求**相反**(目前是不要求退款,line 17 的舊決策註解也是這樣寫),這點要跟 PM/團隊確認是否要變更先前決策(decisions.md 第3列)。以下是規劃:

## 要改的檔案

### 1. `src/Domain/Cancellation.cs`

**Line 8-22 的 `Cancel` 方法邏輯要改:**
- 新增「已取消」判斷:若 `order.Cancelled` 為 true(重複取消),直接回傳原訂單、`RefundRequested: false`,不重複提出退款。
- 若訂單「未出貨、未取消、已付款」→ 取消後 `RefundRequested: true`。
- 若訂單「未出貨、未取消、未付款」→ 取消後 `RefundRequested: false`(維持原行為)。

概念上大致改成:

```csharp
public static CancellationResult Cancel(Order order)
{
    if (order.Shipped)
        return new CancellationResult(order, RefundRequested: false);

    if (order.Cancelled)
        return new CancellationResult(order, RefundRequested: false); // 已取消過，不重複提出退款

    var cancelledOrder = order with { Cancelled = true };
    var shouldRefund = order.Paid; // 已付款訂單取消要提出退款要求
    return new CancellationResult(cancelledOrder, RefundRequested: shouldRefund);
}
```

- **Line 10, 16-19 的註解**要更新,移除「已付款…不提出退款要求」的舊決策說明,改寫成新規則說明;並把「已取消再取消屬未確認行為」的註解移除,改為明確規則說明。

### 2. `tests/DomainTests/Program.cs`

- **Line 13(`v1-3`)**:預期值要反轉 —「已付款取消」應該 `RefundRequested == true`。
- **新增測試**:
  - 已付款訂單「第一次取消」要提出退款(可與修改後的 v1-3 合併驗證)。
  - 已付款訂單「已經是 Cancelled=true 狀態」再呼叫一次 `Cancel`,驗證 `RefundRequested == false` 且訂單狀態不變(不重複提出)。
  - (可選)未付款訂單取消,`RefundRequested` 應維持 `false`,確保沒有動到既有行為。

## 待確認事項
- 目前程式碼原本明確標註「已付款取消不要求退款」是已定案的 decision(decisions.md 第3列),這次需求與其衝突,建議先跟 PM 確認是否正式推翻該決策,再動工。