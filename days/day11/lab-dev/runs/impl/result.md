## 規則 token 與範圍理由

RULES-TOKEN: oc-sdlc-dev-1。依 CLAUDE.md、plan.md 指示，本次只讀取並依據：
- `specs/rules-v2.md`（本票唯一規則來源，BR-01~04、SC-01~07）
- `design-input/scope-handoff.md`、`design-review.md`（範圍與核對結果）
- `runs/tests/tests.txt`（前一步紅燈：僅 SC-03 FAIL，其餘皆 PASS）

範圍限定 `src/Domain/Cancellation.cs`：未修改測試、API、規格，未新增套件或連接金流。RefundRequested 僅為記憶體旗標，不代表已核准的退款業務流程（CLAUDE.md 理由）。

## 改動說明

紅燈原因：SC-03（已付款、未出貨、未取消時應 `RefundRequested=true`）失敗，原程式在未出貨分支永遠回傳 `RefundRequested=false`，只反映 v1 舊規則。

修改 `Cancel` 方法未出貨分支：新增 `refundRequested = order.Paid && !order.Cancelled`，取代原本固定 `false`：
- 已付款且尚未取消 → `true`（對應 BR-03／SC-03、SC-04）
- 已取消（不論是否已付款）→ `false`，不重複提出退款要求（對應 BR-04／SC-06、SC-07）

未強制規定分支檢查順序，僅以結果對齊 SC-01~07 各項 Then 條件；`Order`、`CancellationResult`、`Cancellation` 公開介面未變動。本次未執行測試，由外層 runner 編譯與執行 `tests/DomainTests`。