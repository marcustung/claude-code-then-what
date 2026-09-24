## RULES-TOKEN 與理由

RULES-TOKEN: `oc-sdlc-dev-1`（來源：CLAUDE.md）

不直接連金流的理由（來源：CLAUDE.md 及 specs/rules-v2.md「限制」列）：`RefundRequested` 只是提出退款要求的旗標，實際金流處理是另一份未核准的契約；直接串接會把尚未經 Owner 核准的業務決策帶進這次僅限 Domain 層的修改。specs/rules-v2.md 也明確要求「不連付款服務、不執行退款、`RefundRequested` 只是記憶體旗標」。

已讀來源：CLAUDE.md、plan.md、specs/rules-v2.md、design-input/scope-handoff.md、design-input/design-review.md、既有 `src/Domain/Cancellation.cs`、`tests/DomainTests/Program.cs`。

## 已完成的修改

**`src/Domain/Cancellation.cs`**：在 `Cancel` 中新增「已取消訂單再次取消」分支（BR-04：回傳原訂單、`RefundRequested=false`、不丟例外），並把原本固定回傳 `RefundRequested: false` 改為 `order.Paid`（BR-03，Owner 於 v2 推翻 v1 決定，來源 specs/rules-v2.md 表格第3列）。公開簽名（`Order`、`CancellationResult`、`Cancellation.Cancel`/`Transitioned`）未變動，未新增套件或外部呼叫。

**`tests/DomainTests/Program.cs`**：移除舊的 v1-1~3（其中 v1-3 預期已被 BR-03 推翻），改為 SC-01~SC-07 共 7 個對應 specs/rules-v2.md 的測試。依 design-input/scope-handoff.md 的提醒，每個測試都同時檢查 Then 的所有欄位（`Cancelled`/整體 `Order` 相等 **且** `RefundRequested`），不再只驗證單一欄位。

## 未做/待確認事項

- 未修改 API、規格檔或 CLAUDE.md。
- design-input/scope-handoff.md 提到「NC-02 與 decisions-v2.1 的回應矛盾」及通知相關事項不屬本次 Domain 修改範圍，未處理。
- 本次未執行測試，測試執行由外層 runner 負責。