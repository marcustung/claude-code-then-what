# Day 9 開工前分析（第二輪）

## 0. 版本分層總覽（不可混用）

| 層次 | 檔案 | 狀態 |
|---|---|---|
| 現況程式（v1 快照） | `src/Domain/Cancellation.cs`、`tests/DomainTests/Program.cs` | 事實，已讀到程式碼 |
| 新要求（本票範圍） | `specs/rules-v2.md` | 教學示範中經 Owner 確認（packet-context.md:6），本次要落地 |
| 未決提案（非本票） | `specs/notification-contract-v2.1.md`、`specs/decisions-v2.1.md` | 全列 `proposed`（notification-contract-v2.1.md:4；decisions-v2.1.md:5-12），僅「已出貨取消 409」一列標「沿用」（decisions-v2.1.md:7） |

下文嚴格按此分層引用，不把 proposed 內容當作本次要改的依據。

---

## 1. 現有程式與測試做什麼（v1 事實）

`src/Domain/Cancellation.cs:8-22` 的 `Cancel`：
- `order.Shipped == true` → 原樣回傳 `order`，`RefundRequested=false`（Cancellation.cs:11-14）。
- 否則一律 `order with { Cancelled = true }`，`RefundRequested=false`（Cancellation.cs:20-21）——**不讀 `Paid`，也不讀 `Cancelled`**，不管輸入是否已經 `Cancelled=true` 都會走同一條路徑。
- Cancellation.cs:18-19 的註解已自陳「已取消再取消」是未確認行為、不應據此寫測試。

`tests/DomainTests/Program.cs:11-13` 三個測試（v1-1/v1-2/v1-3），輸入分別為 `(Shipped,Paid,Cancelled)` = `(false,false,false)`、`(true,false,false)`、`(false,true,false)`。**三筆全部 `Cancelled=false`**，目前測試從未餵入 `Cancelled=true` 的輸入，也就是說「已取消再取消」這條路徑完全沒有測試覆蓋，連間接覆蓋都沒有。

`Transitioned`（Cancellation.cs:25）：純比較函式，本包提供的兩個檔案內沒有任何呼叫方引用它。**是否在完整 repo 其他地方被呼叫，本包未提供，不可斷定**（依 packet-context.md:9，找不到應標未提供，不是「確定沒有」）。

---

## 2. BR-03 與 BR-04 的具體交互情境

rules-v2.md:11-12：BR-03（改）依 `Paid` 決定 `RefundRequested`；BR-04（新）規定「已取消再取消」一律維持原狀、`RefundRequested=false`。兩條規則的交會點只有一種輸入組合：**未出貨、已取消、已付款**（rules-v2.md:25 SC-07）。

- 若實作先判斷 `Paid`（BR-03 邏輯）再判斷 `Cancelled`（BR-04 邏輯），或兩個判斷順序沒有讓「已取消」優先短路，「已取消+已付款」的訂單再次取消時會被誤判成 `RefundRequested=true`，違反 SC-07「不重複退款」。
- 「未出貨、已取消、未付款」（SC-06，rules-v2.md:24）則不受此排序問題影響，因為未付款本來就該是 `false`，兩種順序結果相同——**唯一真正能暴露 BR-03/04 順序錯誤的驗收情境是 SC-07**。

**現有測試只驗到**：未取消輸入下的三種組合（未出貨未付款、已出貨、未出貨已付款）。`Cancelled=true` 的輸入（對應 SC-06、SC-07）目前**零覆蓋**，因此這個交互風險目前完全依賴之後新增的測試才能被抓到，不能假設「改了 BR-03 應該不會影響別的地方」。

---

## 3. 不變 / 要改 / 不能順手改 / 待人決定

**不變**
- BR-01 未出貨未取消可取消（rules-v2.md:9）、BR-02 已出貨不可取消（rules-v2.md:10）——皆標「v1 保留」「不變」。
- 三個型別簽名不可改、不連付款/退款服務（rules-v2.md:13「限制」列）。

**要改（rules-v2.md 明確授權）**
- `Cancel` 需依 `Paid` 決定 `RefundRequested`（BR-03，rules-v2.md:11），且需依 `Cancelled` 短路為「維持原狀」（BR-04，rules-v2.md:12），兩者必須一起落地，順序需能通過 SC-07。
- `Program.cs` 的 v1-3（Program.cs:13）斷言需反轉；SC-04/05/06/07 對應測試目前缺席，需新增。

**不能順手改**
- API 層、HTTP 狀態碼、`logs.jsonl`、`/metrics`、`receipts.jsonl`、重試/`dead_letter`——這些只出現在 `notification-contract-v2.1.md`（proposed）與 `decisions-v2.1.md`（proposed），rules-v2.md 未授權連動。**本包沒有提供任何 API/呼叫端檔案，無法判斷完整 repo 是否已有這類實作**（packet-context.md:7），只能說：不在本票範圍、不應順手接上，不是「確定不存在」。
- 三型別簽名（rules-v2.md:13 明文列為 hook 擋點）。

**待人決定（不可由 AI 代為核准）**
- 是否要把 `notification-contract-v2.1.md` 併入本次範圍——目前狀態是 `proposed`，不予核准，留待作者決定（不替人核准通知契約）。
- `notification-contract-v2.1.md:15`「已取消再取消：API 回 200／ok=false **或** 409」與 `decisions-v2.1.md:6`「200 … **而非** 409」的措辭不一致，屬 proposed 文件間的內部落差，與本次 domain 改動無關，但值得回報給作者，由其決定用哪一版。

---

## 4. 第一輪需收回或縮小的結論

| 第一輪主張 | 出處 | 問題 | 應如何收回/縮小 |
|---|---|---|---|
| 「notification-contract-v2.1.md **第16行**」引用 NC-02 的 200/409 敘述 | runs/r1/result.md:62 | 引用行號有誤：NC-02 實際在 `notification-contract-v2.1.md:15`，第16行是 NC-03 | 應更正為第15行，避免設計者照號碼找錯規則 |
| 「目前程式庫**沒有任何對應實作**」（指 API/日誌/metrics 等） | runs/r1/result.md:58 | 逾越本包範圍下結論：packet-context.md:7 明講「不能從未提供 API 或呼叫端，推論完整 repo 沒有那些實作」 | 應縮小為「本包未提供相關檔案，無法判斷是否已存在；即使存在，本票也未授權連動」 |
| 「目前**無任何呼叫方**使用它」（指 `Transitioned`） | runs/r1/result.md:11 | 同樣逾越範圍：packet-context.md:9 明講找不到呼叫方應標未提供，不是斷言不存在 | 應改為「本包兩個檔案內未見呼叫方，完整 repo 是否有其他呼叫方未提供，不可斷定」 |
| 「是否需要為 rules-v2.md **補一份 decisions-v2.md**」列為待人決定問題 | runs/r1/result.md:64, 72 | 暗示應比照 v1/v2.1 的檔名模式補件，貼近 packet-context.md:10 明文禁止的「創造一個必須存在的決策檔名」 | 應縮小為單純記錄「rules-v2.md 沒有像 v1/v2.1 一樣的獨立確認檔」這個文件模式差異，不建議是否要補件或該取什麼檔名 |

其餘結論（v1 行為描述、BR-01/02 不變、BR-03/04 改動範圍、SC-04~07 測試缺口、通知契約 proposed 不併入本票）經逐行核對後**維持不變，可保留**。

---

## 5. 給設計者的交接（不含程式碼）

1. **改動落點**：`Cancellation.cs:8-22` 的 `Cancel` 方法需新增兩個判斷維度——`Cancelled` 是否已為 `true`（BR-04 優先短路，維持原狀）與 `Paid`（BR-03，決定 `RefundRequested`）。**BR-04 的判斷需能在 `Paid` 判斷之前生效**，否則會在「已取消+已付款」情境（SC-07）產生錯誤的 `RefundRequested=true`——這是本次唯一需要特別設計順序的交互點，且現有測試對此零覆蓋。
2. **測試改動**：`Program.cs:13`（v1-3）斷言需反轉為 `RefundRequested=true`；需新增對應 SC-04、SC-05、SC-06、SC-07 四個情境（rules-v2.md:22-25）的測試，其中 SC-07 是唯一能抓出 BR-03/BR-04 順序錯誤的測試，設計時應優先確保。
3. **明確排除**：本次不觸碰任何 API、日誌、metrics、通知佇列相關內容；這些屬 `notification-contract-v2.1.md`（proposed），未經作者核准前不併入本票，本分析亦未替作者核准該契約。
4. **待作者裁定事項**：（a）通知契約要不要納入這次或另開票；（b）`notification-contract-v2.1.md:15` 與 `decisions-v2.1.md:6` 對「重複取消回 200 或 409」的措辭落差，由誰、何時統一。
5. **範圍邊界**：三個型別（`Order`、`CancellationResult`、`Cancel`/`Transitioned` 簽名）不可改（rules-v2.md:13）；不得因為程式碼方便就順勢接上通知或 API 邏輯。

以上為靜態閱讀六份材料與第一輪報告後的核對結果，未執行測試、未修改任何檔案。