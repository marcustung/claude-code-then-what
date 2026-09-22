已讀完 `spec.md`、`audit.md`、`runs/interview-01/result.md`,並核對 `src/Domain/Cancellation.cs`、`tests/DomainTests/Program.cs`、`src/Api/Program.cs`(`graph-project/` 下是 CodeGraph 索引用的副本,依 README.md 說明非實際維護來源,以下只針對根目錄 `src/`、`tests/`)。

## 要改的檔案與行號

### 1. `src/Domain/Cancellation.cs`(核心變更)

- **第 20-21 行**
  現況:
  ```csharp
  var cancelledOrder = order with { Cancelled = true };
  return new CancellationResult(cancelledOrder, RefundRequested: false);
  ```
  改為依 `order.Paid` 決定退款旗標:
  ```csharp
  var cancelledOrder = order with { Cancelled = true };
  return new CancellationResult(cancelledOrder, RefundRequested: order.Paid);
  ```
  依據:`spec.md:4`「已付款取消時提出退款要求」;`spec.md:5`「只調整取消結果旗標…保留既有型別簽名」,`CancellationResult` 簽名不需變。

- **第 10、16-19 行的註解**
  這些註解引用「decisions.md 第2/3/5列」,但本倉庫**沒有 decisions.md**(已用 Glob 確認)。註解內容(「已付款…不提出退款要求」)與 spec.md:4 直接矛盾,屬過時產物,應一併改寫或移除,避免誤導下一位接手者。

- **未解決、暫不動的部分**:`Cancel()` 對 `order.Cancelled == true` 的輸入沒有獨立分支,只檢查 `Shipped`。改成 `RefundRequested: order.Paid` 後,重複取消(idempotent)也會算出 `RefundRequested: true`,但 `Api/Program.cs:73-74` 的 `idempotent` 分支不會觸發通知、不會 `store.Put`——API 回應卻仍會把這個旗標值透傳出去(第89行),造成「回應顯示 true、但實際沒發通知」的不一致。這是 `audit.md` 第一輪 Q1 列出的未決項,**沒有真人 PM 答覆**,不應由本次逕自決定。建議先取得 Owner 對 Q1 選項 (a)/(b)/(c) 的裁決,再決定是否要在 `Cancel()` 或 API 層另外加判斷。

### 2. `tests/DomainTests/Program.cs`

- **第 13 行**
  現況斷言「已付款取消不要求退款」:
  ```csharp
  Check("v1-3", "已付款取消不要求退款", () => { var r = Cancellation.Cancel(new Order(false, true, false)); return r.Order.Cancelled && !r.RefundRequested; });
  ```
  與 spec.md:4 相反,一旦套用上述改動會直接 FAIL,需改寫斷言為「要求退款」:
  ```csharp
  Check("v1-4", "已付款取消要求退款", () => { var r = Cancellation.Cancel(new Order(false, true, false)); return r.Order.Cancelled && r.RefundRequested; });
  ```
  (編號沿用 audit.md 建議,原 v1-3 若保留原始語意會與新規則衝突,應替換而非並存。)

## 建議新增的測試(針對本次需求,不做全系統補測)

1. **未付款取消不要求退款**(補齊對照組,確保 `Paid=false` 分支不受影響):
   ```csharp
   Check("v1-5", "未付款取消不要求退款", () => { var r = Cancellation.Cancel(new Order(false, false, false)); return r.Order.Cancelled && !r.RefundRequested; });
   ```
2. **已出貨、已付款訂單仍不可取消、不要求退款**(確認 `Shipped` 優先於 `Paid`,維持第11-14行既有行為不被新邏輯破壞):
   ```csharp
   Check("v1-6", "已出貨已付款不可取消不要求退款", () => { var o = new Order(true, true, false); var r = Cancellation.Cancel(o); return r.Order == o && !r.RefundRequested; });
   ```

## 不建議這次動的地方

- `src/Api/Program.cs` 全檔(第69-89行透傳邏輯):已核對,`result.RefundRequested` 已完整透傳到 JSON 回應、log、`Notification`、sink payload,只要 `Cancel()` 回傳正確旗標,**API 層不需改**,符合 spec.md:5 的範圍限制。
- 重複取消(idempotent)、併發取消的旗標/原子性問題:`spec.md:6` 明列為未決,`audit.md` 也明確標註「須由適當 Owner 接受風險,不能由模型核准」,本次不應擅自實作或補測試。

以上為所需修改的完整清單;未實際修改程式、未執行測試、未核准開工。