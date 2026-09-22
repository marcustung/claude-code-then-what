## 限制說明
本次僅有 Read/Grep/Glob/Skill 工具、無法派子代理、也不能改碼/跑測試。以下搜尋範圍限定在 `work/` 目錄樹（`spec.md`、`src/`、`tests/`），已用 Glob 確認 `decisions.md` **不存在**於此樹中——但程式碼註解多處引用「decisions.md 第N列」，這是外部文件或已遺失的檔案，本次無法驗證其內容，僅能視為現況程式碼裡的「聲稱」，不當成已接受的規則。

## 現況與影響路徑（附行號）

**spec.md:3-4** — 需求：已付款訂單取消後，要「提出退款要求」讓後續流程知道處理退款；未出貨訂單可取消。

**src/Domain/Cancellation.cs:16-21** — 目前 `Cancel()` 對已付款、未出貨的訂單取消時，`RefundRequested` 永遠回傳 `false`（第21行硬編碼）。註解（第17行）明講這是「已付款、尚未出貨的訂單取消後，不提出退款要求」——**與 spec.md 第4行的新需求直接衝突**。

**src/Domain/Cancellation.cs:18-19** — 已取消訂單再次取消的路徑，註解明確標記「未確認行為…不應據此撰寫測試預期」，目前只是為了滿足簽名回傳同樣結果（`RefundRequested: false`）。

**tests/DomainTests/Program.cs:13** — `v1-3` 測試斷言「已付款取消不要求退款」（`!r.RefundRequested`），這條測試目前編碼的正是**舊行為**，一旦依 spec 修正 `Cancellation.Cancel`，此測試會失敗，需要連動更新。

**src/Api/Program.cs:69-89** — API 層 `/orders/{id}/cancel`：
- 第72行：已出貨 → `outcome="rejected_shipped"`，409，不通知（不受本次影響）
- 第73行：狀態有轉換（`transitioned=true`）→ `outcome="ok"`，200，寫回 store，並觸發通知（第76-85行）
- 第74行：未轉換（例如重複取消同一張已取消訂單）→ `outcome="idempotent"`，200，**不通知**（第76行 `if (transitioned)` 為 false 時跳過整個通知區塊）
- 第89行：回應 body 直接透傳 `result.RefundRequested`，所以 Domain 層的旗標值會直接反映到 API 回應與 log（第88行 `refund_requested = result.RefundRequested`）與通知 payload（第79行 `Notification(... "order_cancelled", result.RefundRequested)`）

**src/Api/Program.cs:79-84** — 通知本體固定用既有 `Notification` record，`Kind` 固定為 `"order_cancelled"`，`RefundRequested` 已是既有欄位——若只是把 Domain 層旗標值改對，通知管線本身不需要新型別或新 event kind 即可把退款要求傳下去。

**spec.md:5** — 範圍聲明：「只調整取消結果旗標，不直接連付款服務；保留既有型別簽名」——已限定本次不修改 `CancellationResult`/`Notification` 的型別簽名，也不呼叫付款服務。

**spec.md:6** — PM 自己列出的三個未決問題：重複取消回傳什麼、併發取消是否入本次範圍、通知是否需要新行為。這些是 spec 本身也沒回答的，屬於本輪要問的核心。

---

以上是現況掃描，不代表我已經和你達成共識。以下是第一輪需要你決定的問題（僅限「已付款取消旗標」這個需求範圍內，不做全系統審計）：

❓ **Q1** - **重複取消一張「已付款、已取消」訂單時，`RefundRequested` 該回傳什麼？**：目前 API 對這個情境會走 `idempotent` 分支（src/Api/Program.cs:74），`Cancellation.Cancel` 對已取消訂單目前不論付款狀態一律回 `RefundRequested:false`（src/Domain/Cancellation.cs:18-21，且程式碼自己標註這段是「未確認行為」）。可能選項：(a) 維持 `false`（第二次呼叫不重複提出退款要求，視為已經處理過一次）、(b) 回傳當初狀態算出的實際值（即已付款則仍為 `true`，讓呼叫端自行判斷是否重複）、(c) 明確定義為不支援／回錯誤，讓上游禁止重複呼叫。

➡️ 我沒有足夠依據替你決定，這正是需要你裁示的地方。

---

❓ **Q2** - **併發取消（同一訂單被兩個請求幾乎同時取消）是否屬於本次範圍？**：`src/Api/Program.cs:63-73` 目前是「先讀 store、算 Cancel 結果、再寫回 store」的 check-then-act 序列，`OrderStore`（src/Api/Program.cs:96-101）只在單一 `Put`/`TryGet` 呼叫內加鎖，整段流程本身不是原子操作，理論上兩個並發請求可能都判定為「可轉換」並各自觸發一次通知與退款旗標。可能選項：(a) 本次不處理，明確記為已知限制、留給之後的票、(b) 本次一併加鎖讓整段 cancel 流程原子化，避免重複觸發退款通知。

➡️ 這決定會影響改動範圍大小，也建議你來定。

---

❓ **Q3** - **通知管線是否需要新行為，還是沿用現有 `order_cancelled` 事件把 `RefundRequested` 傳下去就夠？**：`src/Api/Program.cs:79` 顯示通知本體已經帶有 `RefundRequested` 欄位，只要 Domain 層把值改對，下游即可透過既有事件拿到退款需要處理的訊號，不需新增事件種類或欄位。可能選項：(a) 沿用現有事件即可（最小改動，符合 spec.md:5 的「保留既有型別簽名」）、(b) 需要新增獨立事件/欄位（例如額外的 `refund_requested` 專屬事件），供下游系統做不同的路由或優先處理。

➡️ 依 spec.md:5「保留既有型別簽名」的範圍聲明，傾向 (a)，但這是你的判斷，我不代為拍板。

---

目前這三題彼此獨立、不互相依賴，已構成第一輪的完整前沿。等你回覆後，我會依答案展開下一輪（例如 Q1/Q2 的答案可能牽動測試更新的具體寫法）。在你確認之前，我不會宣稱已達成共識，也不會動手改碼或執行測試。