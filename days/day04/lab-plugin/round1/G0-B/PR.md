# PR #142 取消未出貨訂單（Claude Code 產生，Owner 已確認規則）

## 交接契約
### 1. 可追溯
- 需求／工單版本：ORD-142 v2（2026-09-16 補充退款規則）
- 規則位置：docs/rules/orders.md §R-07「已付款且未出貨的訂單被取消時，系統建立退款申請（RefundRequested=true），實際退款由付款服務依 R-07 處理；未付款訂單不建立退款申請」
- 這次修改的檔案：src/Orders/Cancellation.cs、tests/Program.cs

### 2. 獨立證據
- 驗收預期的規則依據：R-07（已付款取消→RefundRequested=true）；R-02「已出貨訂單不可取消，呼叫端以 Order.Cancelled 未改變判斷」；R-05「重複取消為冪等」
- 實際執行輸出：`dotnet run` 7 組情境 18 個斷言 PASS（.NET 9.0.104，2026-09-16，CI job #8812）

### 3. 語意邊界
- 新增的假設：無（原六條假設已對到 R-02／R-05／R-07，或依 Owner 決定排除：部分付款不在本工單範圍）
- 已確認：R-02、R-05、R-07 由訂單 Owner（@order-owners）於 2026-09-16 在 ORD-142 留言確認；已出貨取消不丟例外由 Owner 同意（呼叫端檢查 Cancelled）
- 待確認：無

### 4. 影響範圍
- 呼叫端：OrdersController.CancelAsync（唯一呼叫端，見 grep 結果附於 ORD-142）
- 權限／資料來源：無變更
- 尚未驗證的路徑：無

### 5. 可解釋（Reviewer 填）
- 接受範圍：全部；理由：三條規則有來源，測試預期對得回 R-02／R-05／R-07
- 負責人：規則＝訂單 Owner；修正＝作者；判定＝Reviewer

---
判級（作者自評）：`owner-required`（已由 Owner 審過）
觸及：[x] 金額／付款  [ ] 授權／權限  [x] 狀態轉換規則
AI 產生的部分：[x] 程式  [x] 測試
