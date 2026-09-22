已讀完 `spec.md`、`src/Domain/Cancellation.cs`、`src/Api/Program.cs`、`tests/DomainTests/Program.cs`。以下只針對「已付款訂單取消後要提出退款要求」這件事，不做其他範圍的檢視。

## 需要改的地方

### `src/Domain/Cancellation.cs`
- **第 17 行**註解「已付款、尚未出貨的訂單取消後，不提出退款要求（decisions.md 第3列）」與 spec 第 4 行「已付款取消時提出退款要求」直接矛盾，需刪除或改寫。
- **第 20–21 行**是唯一要動的邏輯：
  ```csharp
  var cancelledOrder = order with { Cancelled = true };
  return new CancellationResult(cancelledOrder, RefundRequested: false);
  ```
  改成：
  ```csharp
  var cancelledOrder = order with { Cancelled = true };
  return new CancellationResult(cancelledOrder, RefundRequested: !order.Cancelled && order.Paid);
  ```
  用 `!order.Cancelled && order.Paid` 而非單純 `order.Paid`，是為了讓「已取消訂單再次取消」時的旗標維持原本行為（仍是 `false`）。因為 spec 明講「重複取消應回傳什麼」尚未決，第 18–19 行的既有註解已經寫明「此處僅為滿足簽名，不應據此撰寫測試預期」——這次修改不應該連帶改變那段未決行為，只調整「未出貨、尚未取消 → 真正轉成已取消」這條路徑上的退款旗標。
  - 型別簽名（`CancellationResult`、`Cancel` 的參數/回傳型別）不變，符合 spec 範圍限制。

- 順帶一提：註解中引用的 `decisions.md` 我用 Glob 找不到這個檔案，程式碼多處引用它（第 10、16、17、18 行），建議跟 PM/RD 確認這份文件是否存在於別處，否則這些註解的可追溯性有問題（不影響這次改動，但值得提醒）。

### `src/Api/Program.cs`
不需要改。`refund_requested`（第 89 行）與通知的 `RefundRequested`（第 79 行）都是直接取用 `result.RefundRequested`，邏輯已經會自動跟著 `Cancellation.Cancel` 的新結果走。

## 測試要改 / 新增（`tests/DomainTests/Program.cs`）

1. **改第 13 行（v1-3）**：現在斷言「已付款取消不要求退款」，要改成反過來：
   ```csharp
   Check("v1-3", "已付款取消提出退款要求", () => { var r = Cancellation.Cancel(new Order(false, true, false)); return r.Order.Cancelled && r.RefundRequested; });
   ```

2. **新增：未付款取消不要求退款**（目前 v1-1 只驗證 `Cancelled`，沒明確驗證 `RefundRequested`）：
   ```csharp
   Check("v1-4", "未付款取消不要求退款", () => { var r = Cancellation.Cancel(new Order(false, false, false)); return r.Order.Cancelled && !r.RefundRequested; });
   ```

3. **新增：已出貨已付款不可取消，也不要求退款**（鎖住範圍邊界，確認已出貨規則不受這次改動影響）：
   ```csharp
   Check("v1-5", "已出貨已付款不可取消也不要求退款", () => { var o = new Order(true, true, false); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
   ```

**不建議新增**「已取消的已付款訂單再次取消」的退款旗標測試——spec 明確列為未決項，且原始程式註解已寫明不應據此撰寫測試預期，維持現況即可。

## 小結
- 只需改 `Cancellation.cs` 第 17、20–21 行（邏輯+註解）。
- `Program.cs`（API）不用改。
- `DomainTests/Program.cs` 改 1 個既有測試（v1-3）、建議新增 2 個測試（未付款不退款、已出貨不受影響）。
- 待確認事項：`decisions.md` 檔案下落；重複取消/併發取消不在本次範圍。