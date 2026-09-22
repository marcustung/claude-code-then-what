## 目前行為（src/Domain/Cancellation.cs，v1 快照 @885e521）

| # | 行為 | 位置 |
|---|---|---|
| A1 | `Shipped=true`：回傳原 order，`RefundRequested=false`，不丟例外 | Cancellation.cs:11-14 |
| A2 | `Shipped=false`：一律設 `Cancelled=true`，`RefundRequested` 恆為 `false`（不看 `Paid`） | Cancellation.cs:20-21 |
| A3 | 已取消（`Cancelled=true`）且未出貨的訂單再次取消：**沒有獨立分支**，會落入 A2 同一段邏輯，重新產生 `Cancelled=true` 的新 record，`RefundRequested=false`。程式碼註解明講這是「未確認行為，不應據此撰寫測試預期」 | Cancellation.cs:18-19 |
| A4 | `Transitioned()` 只是比對 before/after，非業務規則；本檔內、tests/Program.cs 內都沒有 caller | Cancellation.cs:24-25 |
| A5 | 既有測試只有 3 個，對應 decisions-v1.md 的三條「已確認」條件，沒有涵蓋 BR-03/BR-04/SC-05~07 | tests/DomainTests/Program.cs:11-13 |

（事實，直接讀自程式碼與測試檔）

## 新要求（specs）

- **decisions-v1.md**：三條已確認 + 一條明確標「已取消再取消＝待確認/受阻範圍」（decisions-v1.md:9）。（事實）
- **rules-v2.md**：
  - BR-03（改）：已付款＋未出貨取消 → `RefundRequested=true`（rules-v2.md:11, SC-03 line 21）
  - BR-04（新）：已取消再取消 → 維持原狀、`RefundRequested=false`、不丟例外（rules-v2.md:12, SC-06/07 line 24-25）
  - 檔頭自稱「唯一規則來源」且「由訂單 Owner 於教學示範中確認」（rules-v2.md:3）
- **notification-contract-v2.1.md / decisions-v2.1.md**：NC-01~07 通知契約，明確標 `proposed`（notification-contract-v2.1.md:4-5；decisions-v2.1.md 全表皆為 proposed）。packet-context.md 明講「不代表納入本次 domain 修改」（packet-context.md:6）。

## 差異清單

**差異1｜BR-03 退款方向相反**
現況 A2（RefundRequested 恆 false）vs rules-v2 BR-03（Paid=true 時應為 true）。
- 來源：Cancellation.cs:21 vs rules-v2.md:11
- 分類：**事實**（程式碼與文件文字確有出入）。但「rules-v2.md 是否為本次要採納的需求」是**待確認**——packet-context.md 只稱它是「後續教學需求」，且明講文件內 Owner 是教學角色、不等於使用者本次核准（packet-context.md:5）。不能把 rules-v2 直接當本次已核准需求。

**差異2｜已取消再取消的處理方式**
現況 A3 是覆寫式重設（產生新 record，不保留原值），且原碼註解自承未驗證；rules-v2 BR-04 要求維持原 record 不變。
- 來源：Cancellation.cs:18-21 vs rules-v2.md:12、SC-06/07 (rules-v2.md:24-25)
- 分類：**事實**存在差異；但 decisions-v1.md 早已把這項標為「待確認/受阻範圍」（decisions-v1.md:9），rules-v2 是否真的解除此阻擋，屬於**待確認**（同差異1的授權問題）。

**差異3｜測試覆蓋缺口**
tests/Program.cs 只有 v1 三項，沒有任何對應 BR-03/BR-04/SC-05 的測試。
- 來源：tests/DomainTests/Program.cs:11-13 vs rules-v2.md 的 SC 表（rules-v2.md:19-25）
- 分類：**事實**。至於「是否本來就該在別處有 v2 測試檔但沒提供」——**未提供不能推論成不存在**，只能標「未提供」。

**差異4｜通知行為**
現況完全沒有通知/事件發佈機制；NC-01~07 若要實作需要新的介面。
- 來源：Cancellation.cs 全檔 vs notification-contract-v2.1.md
- 分類：**推論**（此文件本身標 proposed，尚未接受，不構成「新要求對現況的差異」，只是潛在未來差異，不列入本次要改範圍）。

## 「只改最直覺一處」仍會出錯的情境

最直覺的修法是把 A2 那行改成：
```csharp
return new CancellationResult(cancelledOrder, RefundRequested: order.Paid);
```
這樣 SC-01/03/04（未取消訂單的取消）會過。但 BR-04／SC-07 要求「已取消、已付款」的訂單再次取消時 `RefundRequested` 必須是 `false`（不重複退款）。因為程式碼沒有針對 `order.Cancelled=true` 的分支，`Cancelled=true, Paid=true` 的訂單再次呼叫 `Cancel` 時，會算出 `RefundRequested=order.Paid=true`，**違反 SC-07**，且也沒有「維持原 record 不變」（BR-04 的另一半要求）。也就是說：只修 BR-03 那一行，會讓 BR-04/SC-06/SC-07 全部壞掉，因為兩條規則共用同一段「未出貨」分支，缺一個「已取消」的前置判斷。

## 整理

**要改**（僅在使用者/業務 Owner 明確核准 rules-v2 為本次範圍後）：
- BR-03：`RefundRequested` 依 `order.Paid` 判斷
- BR-04：新增「已取消」前置分支，回傳原 record、`RefundRequested=false`

**不改**（本次範圍外，文件本身標明未接受）：
- notification-contract-v2.1.md 的 NC-01~07
- decisions-v2.1.md 中所有 `proposed` 項目（API 回應碼、重試策略、儲存方式、v1.1.0/v1.2.0 修復等）

**缺少的驗收**：
- rules-v2.md 有 SC-01~07 表格，但沒有對應的 tests/Program.cs 測試程式碼可核對——目前測試檔仍是 v1 三項
- SC-05（已出貨＋已付款）在現有測試中沒有對應案例（現有測試 v1-2 只測了 Paid=false）
- 通知契約若日後被接受，`receipts.jsonl`／`/metrics` 等觀測面完全沒有任何實作或測試線索

**需要誰決定**：
- rules-v2.md 是否為本次要採納的正式需求，還是僅供參考的教學材料——packet-context.md 明講該文件內「Owner」是教學角色、不代表使用者本次核准，這需要使用者本人明確表態
- decisions-v1.md 中「已取消再取消」原本標為待確認/受阻——是否用 BR-04 的做法解除阻擋，需業務方/使用者裁示，不能由我方逕自認定已確認
- notification-contract-v2.1.md／decisions-v2.1.md 全數 proposed，是否接受、何時接受，需要使用者（作者）決定