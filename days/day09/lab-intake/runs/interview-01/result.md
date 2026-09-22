## 現況（附行號）

**spec.md:3-4** — 需求：已付款訂單取消後，「讓後續流程知道需要處理退款」；未出貨訂單可取消，已付款取消時提出退款要求。

**src/Domain/Cancellation.cs:16-21** — `Cancel()` 目前對未出貨訂單一律回傳 `RefundRequested: false`，**不論 `order.Paid` 為何**。第17行註解寫「已付款、尚未出貨的訂單取消後，不提出退款要求（decisions.md 第3列）」——但本專案沒有 decisions.md，且與 spec.md:4 的需求直接矛盾。這是本次要動的核心行。

**src/Domain/Cancellation.cs:18-19（註解）** — 明白標註「已取消的訂單再次取消屬於未確認行為（待確認），此處僅為滿足簽名回傳同樣結果，不應據此撰寫測試預期」。也就是說 `Cancel()` 對 `order.Cancelled == true` 的輸入沒有專門分支，只檢查 `Shipped`。

**tests/DomainTests/Program.cs:13** — v1-3 測試斷言「已付款取消不要求退款」（`!r.RefundRequested`），與 spec.md:4 相反，一旦照 spec 修正 `Cancel()`，此測試會失敗。

**src/Api/Program.cs:69-89** — API 層已經把 `result.RefundRequested` 全程透傳：
- 第79行組 `Notification` 時帶入 `result.RefundRequested`
- 第89行 API 回應 JSON 帶 `refund_requested`
- 第88行 log 一行也記 `refund_requested`
- NotificationWorker 送到 sink 的 payload（第200、231行）也已包含 `refund_requested` 欄位

即：**只要 `Cancellation.Cancel()` 回傳正確的旗標，API/通知/log/sink payload 都不用改**，這與 spec.md:5「只調整取消結果旗標，不直接連付款服務；保留既有型別簽名」一致。

**src/Api/Program.cs:73-74** — `transitioned` 只在「未取消→已取消」這次真的翻轉時才成立；`idempotent`（重複取消）分支完全不進入通知邏輯，也不會 `store.Put`。但 API 回應（第89行）仍會把 `result.RefundRequested`（來自對已取消訂單再跑一次 `Cancel()` 的結果）放進 JSON——若 `Cancel()` 之後看 `Paid` 給 true，重複取消的回應會顯示 `refund_requested: true`，即使沒有觸發任何通知。

**限制說明**：本輪僅用 Read/Grep/Glob 唯讀檢視 `src/`、`tests/`，未執行子代理、未跑測試、未修改任何程式碼或核准開工；範圍僅限本次取消退款旗標需求，未做全系統審計。

---

## 第一輪問題（frontier）

❓ **Q1 - 重複取消（idempotent）時 `RefundRequested` 該回傳什麼？**：對已經 `Cancelled=true` 的付款訂單再次呼叫 `/orders/{id}/cancel`，`Program.cs:73-74` 判定為 `idempotent`，不會發通知、不會更新 store。但 API 回應仍會帶 `result.RefundRequested`。選項：
(a) 一律回傳 `false`（語意：這次呼叫沒有新動作，欄位反映「本次是否需要處理」）；
(b) 依訂單當下 `Paid` 狀態計算（可能造成 `refund_requested: true` 但實際沒發通知的不一致觀感）；
(c) 回傳「上一次真正取消時」的歷史結果（需要 `OrderStore` 增加歷史欄位，屬於資料結構變更）。

➡️ 建議 (a)：與「本次沒有新翻轉」的語意一致，且不需改動 `OrderStore` 結構，維持 spec.md:5「保留既有型別簽名」的最小改動範圍。

---

❓ **Q2 - 併發取消是否列入本次範圍？**：`Program.cs:63,69,73` 的 `TryGet → Cancel → Put` 不是原子操作；若兩個請求同時打同一張已付款訂單，可能都判定為 `transitioned`，各自產生一則退款通知（重複退款請求風險）。spec.md:6 明確把「併發取消是否屬本次範圍」列為未決。選項：
(a) 本次不處理，維持現狀（沿用既有 non-atomic 行為，風險留給後續票）；
(b) 本次一併修正為 atomic check-and-set，避免重複退款通知。

➡️ 建議 (a)：spec.md 範圍聲明是「只調整取消結果旗標」，且此為既有架構問題、非本次新增，建議另開票處理，避免範圍蔓延。

---

❓ **Q3 - 通知是否需要新行為，還是只需旗標值改變？**：`refund_requested` 欄位已存在於 `Notification`（Program.cs:79）、log（88行）、送往 sink 的 payload（200、231行），`Kind` 目前固定為 `"order_cancelled"`。若把旗標從固定 `false` 改成依 `Paid` 計算，下游收到 `refund_requested: true` 時是否足以「知道需要處理退款」？選項：
(a) 沿用現有欄位與 `Kind`，不新增通知種類（純粹旗標值變化）；
(b) 需要新增獨立的通知種類或欄位（例如 `Kind = "refund_requested"`），因下游消費邏輯可能只看 `Kind` 不看欄位值。

➡️ 建議 (a)，但這需要 RD 確認下游（sink/接收端）目前實際怎麼消費這個 payload——這點程式碼看不出來，需負責人告知或另外調查下游服務。

---

❓ **Q4 - 現有測試 v1-3（tests/DomainTests/Program.cs:13）是否確認視為過時、需一併替換？**：該測試與 `Cancellation.cs:16-19` 的註解一起，斷言「已付款取消不要求退款」，與 spec.md:4 相反。確認：
(a) 是，該測試連同對應註解（引用不存在的 decisions.md 第3列）視為過時，本次一併改寫；
(b) 否，該測試代表某個尚未告知的既有約定，本次改動需先釐清為何存在此斷言。

➡️ 建議 (a)：spec.md:7 已明確聲明「現有程式只代表現況，不能把它當成草案已接受的規則」，該測試與註解的依據（decisions.md）在本倉庫中不存在，判斷為過時產物。

---

以上為第一輪問題，尚未取得負責人回覆，暫停於此，不代表已達成共同理解。