## 現況（含檔案行號)

**spec.md** (spec.md:3-6)：目的是「已付款的訂單取消後，讓後續流程知道需要處理退款」；範圍限定「只調整取消結果旗標，不直接連付款服務；保留既有型別簽名」；並列出三項未決：重複取消回傳什麼、併發取消是否入本次範圍、通知是否需要新行為。

**現行程式行為**：
- `Cancellation.Cancel`（src\Domain\Cancellation.cs:8-22）目前不論 `order.Paid` 為何，`RefundRequested` 一律回傳 `false`（第 13、21 行），且註解明白寫「已取消的訂單再次取消屬於未確認行為…不應據此撰寫測試預期」（Cancellation.cs:18-19）。
- 出貨判斷在付款判斷之前短路（Cancellation.cs:11-14）：已出貨訂單直接原樣退回，不看 `Paid`。
- API 層（src\Api\Program.cs:69-89）把 `result.RefundRequested` 原樣往下傳三處：寫入 `logs.jsonl`（Program.cs:88 的 `refund_requested`欄位）、寫入 HTTP 回應 JSON（Program.cs:89）、以及當 `transitioned==true` 時組進 `Notification` 送進 channel／同步發送（Program.cs:79、200、231），最終 POST 給 `OC_SINK_URL`。
- 若 `transitioned==false`（含 idempotent 重複取消路徑，Program.cs:74）則完全不建立通知、不呼叫 `RefundRequested`下游（不 notify，對應程式碼裡標註的 NC-02）。
- 既有測試 `v1-3`（tests\DomainTests\Program.cs:13）目前**斷言**「已付款取消**不**要求退款」（`!r.RefundRequested` 為真），這與 spec 的新需求方向直接衝突。

**限制聲明**：目前工具集僅有 Read/Grep/Glob/Skill，我沒有子代理可派工，以上是我自己唯讀搜尋（Glob 全庫 + Read 四個檔案）得到的結果，未執行測試、未修改程式碼。搜尋範圍已涵蓋 src、tests、spec 全部檔案（共 7 個原始檔），未發現其他涉及 `RefundRequested` 的程式碼位置。

---

以下是第一輪（唯一一輪，本次為無真人回答的單輪示範）需要負責人決定的問題。尚未達成共識，僅列出問題與建議，不代表已核准或已理解一致，請等待回答後才能進入下一輪或開工。

❓ **Q1** - **RefundRequested 觸發條件**：`Cancellation.Cancel`（Cancellation.cs:20-21）目前無論 `Paid` 為何都回傳 `RefundRequested: false`。新需求要「已付款取消時提出退款要求」，但「取消時」具體指哪個狀態轉換？
- A. 僅當 `order.Paid == true` 且**本次呼叫確實從未取消轉為已取消**（即 `Transitioned` 為 true，Cancellation.cs:25）時，才回傳 `RefundRequested: true`。
- B. 只要 `order.Paid == true`，不論是否本次才轉態（包含對已取消訂單重複呼叫）都回傳 `true`。

➡️ 建議 A：對齊 spec 字面「取消後」，且與 API 層現行「只有 transitioned 才建立通知」的邏輯（Program.cs:74-85）一致，不需改動通知觸發時機。

---

❓ **Q2** - **重複取消（訂單已是 Cancelled）時 RefundRequested 該回什麼**：spec 明確列為未決（spec.md:6）。目前 idempotent 路徑（Program.cs:74）不會建立通知，也不會把 `RefundRequested` 往下游送。
- A. 回傳 `false`（不重複提出退款要求），維持「idempotent 不觸發下游」的現行模式。
- B. 依訂單目前的 `Paid` 狀態重新判斷（若 Paid 為 true 則仍回傳 `true`），即使不會被 API 層用來通知。

➡️ 建議 A：避免下游誤解成「又要求一次退款」，且與現行 API 層不對 idempotent 結果採取行動的模式一致。

---

❓ **Q3** - **併發取消是否納入本次範圍**：`OrderStore`（Program.cs:96-101）的 `Put`/`TryGet` 各自用鎖保護，但「讀取 → 判斷 → 寫回」（Program.cs:63-73）整體並非原子操作，兩個並發的取消請求可能都判定為「本次轉態」。
- A. 排除在本次範圍外，維持現況（spec.md:5 只要求調整旗標，不改動型別簽名／不擴大範圍）。
- B. 納入，需要額外的並發保護（例如 CAS 或每訂單鎖）確保只有一次轉態與退款請求。

➡️ 建議 A：spec 範圍明確限定「只調整取消結果旗標」，且此為既有架構限制而非本次需求引入的新問題，建議記錄為已知限制，另案處理。

---

❓ **Q4** - **通知是否需要新行為**：`Notification` record（Program.cs:94）與 worker 送給 sink 的 payload（Program.cs:200、231）已經有 `RefundRequested` 欄位（Notification.cs 對應成員），目前恆為 `false`。
- A. 不需要新行為，沿用現有 `kind="order_cancelled"` 事件與既有 `refund_requested` 欄位，值會隨 Q1 結果變動即可，下游 sink 不需新增事件類型。
- B. 需要新行為，例如新增獨立事件（如 `kind="refund_requested"`）或改變 schema，讓下游能單獨訂閱退款請求事件。

➡️ 建議 A：現有欄位已足以承載此資訊，且 spec.md:5 要求「不直接連付款服務、保留既有型別簽名」，傾向最小改動。

---

以上四題為本輪應由負責人決定的問題，尚未取得回答，尚未達成共識，暫停於此，不進行下一輪、不修改程式、不執行測試、不核准開工。