## 回報

**RULES-TOKEN: oc-sdlc-dev-1**（來源：CLAUDE.md:2）

**不直接連金流的理由**（來源：CLAUDE.md:5）：RefundRequested 只是提出要求，金流是另一份契約；直接連金流會把未核准的業務決策帶進本次修改。design-input/scope-handoff.md「限制」列也重申：不連付款服務、不執行退款、RefundRequested 只是記憶體旗標。

已讀 plan.md、specs/rules-v2.md、design-input/scope-handoff.md、design-input/design-review.md、src/Domain/Cancellation.cs、tests/DomainTests/Program.cs。

## 修改內容
只改了 `tests/DomainTests/Program.cs`，把舊的 v1-1/v1-2/v1-3 三個測試換成 SC-01～SC-07，逐條依 specs/rules-v2.md 的 Given/Then 撰寫，每個 Then 欄有幾個條件就檢查幾個（不只挑一個欄位）：

- SC-01：`Cancelled=true` 且 `RefundRequested=false`
- SC-02：`Order == o`（同一 record 值，Then 欄未列 RefundRequested 故不查該欄）
- SC-03：`Cancelled=true` 且 `RefundRequested=true`——**與舊 v1-3 預期相反**，來源 specs/rules-v2.md BR-03（改）/SC-03，design-input/scope-handoff.md「要改」第1點確認是 Owner 對 v1 第3列的推翻，非把舊行為當 bug 追認
- SC-04：`RefundRequested=false`（Then 欄只列此項）
- SC-05：`Order == o` 且 `RefundRequested=false`
- SC-06：`Order == o` 且 `RefundRequested=false`（不丟例外由 `Check` 的 try/catch 覆核）
- SC-07：`Order == o` 且 `RefundRequested=false`

未動 Domain、API、規格、CLAUDE.md，未新增套件或外部呼叫。

## 對現有（舊）Domain 執行的預期結果
只依現有 `src/Domain/Cancellation.cs` 邏輯推演（未實際執行，測試由外層 runner 執行）：

- SC-01、SC-02、SC-04、SC-05、SC-06、SC-07：預期 **PASS**——舊 Domain 恆回傳 `RefundRequested=false`，且對已取消訂單重算 `Cancelled=true` 時值等於原訂單，符合這幾條 Then。
- **SC-03：預期 FAIL**——舊 Domain 未依 BR-03（改）在已付款、未出貨時把 `RefundRequested` 設為 `true`，仍恆回傳 `false`。

此推演僅供對照 spec 差異，非執行證據；無執行工具，不宣稱已跑過。