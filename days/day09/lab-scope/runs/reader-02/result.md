# 分析結果

範圍聲明：本次分析目標是 **specs/rules-v2.md**（BR-03、BR-04）。`notification-contract-v2.1.md` 與 `decisions-v2.1.md` 是另一個較晚、狀態為 `proposed` 的提案，僅用於辨識文件邊界，**不併入本次 domain 修改分析**。rules-v2.md 本身雖標「訂單 Owner 於教學示範中確認」，但那是**教學角色**的確認，不等於公司正式核准；本輪僅做分析，不動程式。

---

## 1. 目前行為（事實，來自程式碼）

| 行為 | 位置 | 規則來源 |
|---|---|---|
| `order.Shipped == true` → 回傳原訂單、`RefundRequested=false`、不丟例外 | `src/Domain/Cancellation.cs:11-14` | decisions-v1.md 第2列 |
| `order.Shipped == false` → 一律回傳 `Cancelled=true`、`RefundRequested=false`（**不論 `Paid`、不論 `Cancelled` 是否已為 true**） | `src/Domain/Cancellation.cs:20-21` | decisions-v1.md 第1、3列 |
| 已取消訂單再次取消時的行為 | 程式碼未做任何特判 | decisions-v1.md 第5列標「待確認」；程式碼註解（`Cancellation.cs:18-19`）明說「不代表已驗證或已確認，不應據此撰寫測試預期」 |
| v1 測試只覆蓋 3 個情境（未出貨可取消／已出貨不可取消／已付款取消不要求退款） | `tests/DomainTests/Program.cs:11-13` | — |

## 2. 新要求（rules-v2.md，事實）

| 規則 | 內容 | 位置 |
|---|---|---|
| BR-03（改） | 已付款＋未出貨＋取消 → `RefundRequested=true`；未付款則仍 `false` | `specs/rules-v2.md:11` |
| BR-04（新） | 已取消訂單再次取消 → 維持原狀、`RefundRequested=false`、不丟例外 | `specs/rules-v2.md:12` |
| 限制（沿用） | 不連付款服務、不執行退款、三個型別簽名不可改 | `specs/rules-v2.md:13` |
| 驗收場景 SC-01～SC-07 | 逐欄 Given/When/Then | `specs/rules-v2.md:19-25` |

## 3. 差異（v1 行為 vs v2 要求）

| # | Given | 目前輸出（v1 程式碼實際跑法） | v2 要求輸出 | 差異 |
|---|---|---|---|---|
| SC-03 | 未出貨、已付款、未取消 | `Cancelled=true, RefundRequested=false` | `Cancelled=true, RefundRequested=true` | **不符**，需改 BR-03 |
| SC-04 | 未出貨、未付款、未取消 | `Cancelled=true, RefundRequested=false` | 同上 | 符合，不用改 |
| SC-06 | 未出貨、已取消、未付款 | 程式仍會把 `Cancelled` 設一次 true（本已是 true），`RefundRequested=false` | 原訂單、`RefundRequested=false` | 表面值相符，但**沒有防重機制**，屬巧合過關（見第4節分析） |
| SC-07 | 未出貨、已取消、已付款 | 目前程式碼（未改 BR-03 前）回傳 `RefundRequested=false` | 要求 `RefundRequested=false` | 目前**恰好**符合，但若照最直覺方式改 BR-03，會在此壞掉（見下） |
| SC-01/02/05 | — | 與 v1 一致 | 與 v1 一致 | 無差異 |

## 4. 事實 / 推論 / 待確認

**事實**
- rules-v2.md 明確寫「本檔是這張票唯一的規則來源」（`specs/rules-v2.md:3`）。
- 目前程式碼完全沒有對 `order.Cancelled` 做任何檢查分支。
- `Order` 為 record，`==` 是值比較（非參照比較），v1-2 測試已用此特性斷言。

**推論（非規格明文，僅為程式行為的合理解讀）**
- 若僅將 `Cancellation.cs:21` 的 `RefundRequested: false` 改成 `RefundRequested: order.Paid`，可讓 SC-03、SC-04 通過，但**不會**觸及 BR-04 要求的「已取消不重複判定」邏輯——因為原本就沒有這段邏輯，BR-04 是全新需求，不是修飾既有分支。

**待確認（不可自行判定）**
- decisions-v1.md 第5列「已取消訂單再次取消：尚未確認」在 v1 是明確待確認項；rules-v2.md 雖補了 BR-04，但**正式核准**狀態不在 rules-v2.md 本身可查（該檔僅標「訂單 Owner 於教學示範中確認」，屬教學角色，非公司正式流程）。
- `spec-v1.md`（rules-v2.md 開頭提及的承接文件）本次未提供，不能推論其不存在或內容為何。

## 5. 「只改最直覺一處仍會出錯」的情境

**最直覺的改法**：只把 `Cancellation.cs:21` 的 `RefundRequested: false` 改成 `RefundRequested: order.Paid`，其餘不動（不加 `order.Cancelled` 的判斷分支）。

```csharp
var cancelledOrder = order with { Cancelled = true };
return new CancellationResult(cancelledOrder, RefundRequested: order.Paid); // 唯一改動處
```

逐欄核對 SC-06 / SC-07（BR-04 情境，Given 都是「未出貨、**已取消**」）：

| 欄位 | SC-06 Given | SC-06 期望 | 此改法實際輸出 | SC-06 結果 | SC-07 Given | SC-07 期望 | 此改法實際輸出 | SC-07 結果 |
|---|---|---|---|---|---|---|---|---|
| Shipped | false | — | — | — | false | — | — | — |
| Paid | false | — | — | — | **true** | — | — | — |
| Cancelled（輸入） | true | — | — | — | true | — | — | — |
| Order.Cancelled（輸出） | — | true（原狀，值同輸入） | true | 相符（值相等，巧合） | — | true（原狀） | true | 相符 |
| RefundRequested（輸出） | — | **false** | `order.Paid` = false | **相符（巧合）** | — | **false** | `order.Paid` = **true** | **✗ 不符，此處出錯** |
| 是否丟例外 | — | 否 | 否 | 相符 | — | 否 | 否 | 相符 |

**結論**：SC-06 因為 `Paid=false` 而「意外」通過，掩蓋了 BR-04 沒有真的被實作的事實；SC-07 因為 `Paid=true` 直接暴露 bug——已取消的訂單再次取消，若剛好是已付款單，會被誤判成「這次成功取消並要求退款」，等於**對已經取消的訂單重複觸發退款旗標**。只改 BR-03 那一行，看似最小、最直覺，但因為完全沒有處理 `order.Cancelled == true` 的短路邏輯，BR-04 實質上沒有被實作，只是被 SC-06 的特定輸入僥倖蓋過去。

## 6. 整理

**要改**
- `Cancellation.cs` 的取消分支需要新增對 `order.Cancelled == true` 的判斷（BR-04），並在該分支下維持 `RefundRequested=false`、回傳原狀，**且不能與 BR-03 的退款判斷共用同一段未分流的邏輯**。
- BR-03 的退款判斷（`RefundRequested = order.Paid`）僅能套用在「原本未取消、本次真的完成轉換」的分支。

**不改**
- BR-01、BR-02、型別簽名、不連外部服務等限制（rules-v2.md 明列「不變」／「沿用」）。
- `Transitioned` 輔助函式簽名（規格未要求變更；但其邏輯是否已涵蓋 BR-04 情境待驗證，非本次分析範圍內下定論）。

**缺少的驗收（rules-v2.md 內未覆蓋，需另行確認）**
- 沒有對「已取消＋已付款＋再次取消，多次連續呼叫」的驗收（僅有單次呼叫的 SC-06/07）。
- 沒有對 `tests/DomainTests/Program.cs` 是否已依 SC-01～07 補齊 7 條測試的驗收（目前只讀到 v1 三條，v2 測試是否存在**未提供**，不能推論成不存在）。

**需要誰決定**
- rules-v2.md 標示「教學示範中的 Owner 角色確認」，是否等同公司正式核准，需使用者／實際業務 Owner 明確界定；本分析不能替代此決定。
- decisions-v1.md 第5列「已取消再取消」原列為「待確認」，rules-v2.md 的 BR-04 是否視為該待確認項的正式結案，也需使用者確認（本檔只講「補 v1 待確認項」，未寫明是否等同解除待確認狀態的正式流程）。
- notification-contract-v2.1.md／decisions-v2.1.md 全數標記 `proposed`，是否要納入任何後續範圍，需另行單獨決策，與本次 rules-v2.md 無關。