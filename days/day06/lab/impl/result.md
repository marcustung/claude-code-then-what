All three confirmed acceptance conditions pass.

## 整理

**驗收條件**（依 decisions.md）
1. 尚未出貨、尚未取消可取消，`Cancelled=true` — 已確認並實作
2. 已出貨不可取消，維持原訂單、不丟例外 — 已確認並實作
3. 已付款取消後不提出退款要求（`RefundRequested=false`）— 已確認並實作
4. 不呼叫付款/退款服務 — 本實作全程無外部呼叫，符合限制

**修改位置**
- `Cancellation.cs`：實作 `Cancel`，每個分支以中文註解標出對應 spec.md / decisions.md 來源
- `Program.cs`：新增 3 項對應上述已確認條件的 PASS/FAIL 測試

**驗證方式與結果**（已實際執行）
```
dotnet run --project Demo.csproj
PASS 尚未出貨可取消
PASS 已出貨不可取消
PASS 已付款取消不要求退款
PASS: 全部條件通過
```
回傳碼 0。

**未決事項**
- 「已取消的訂單再次取消」（decisions.md 第5列）尚未確認，屬受阻範圍。程式碼中此路徑僅為滿足函式簽章而回傳同樣結果（未變更為新的取消狀態異常，也未拋例外），並在程式碼中加註明確標示此非已驗證行為，**未**為它撰寫測試預期，等待 Owner 確認後再補上正式行為與測試。