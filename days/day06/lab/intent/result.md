## 對照結果

**intent.md 的目的仍未確認：**
- 誰要取消訂單、現況卡在哪裡 → 待確認
- 想改善什麼指標（改善前後怎麼比較）→ 待確認
- 取消與退款的責任分界 → 尚未決定
- 誰有權確認目的與範圍 → 尚未決定

**spec.md 已經把交付內容寫死了：**
- 工單需求只有一句「讓使用者可以取消尚未出貨的訂單」
- 但骨架已經定義了 `CancellationResult(Order Order, bool RefundRequested)` —— 這暗示「取消」隱含要處理退款旗標，可是 intent.md 明確寫「取消與退款的責任分界」還沒決定，也限制「不執行退款」

**主要落差：**
Spec 把「做出取消功能」直接落地成程式簽名（含 `RefundRequested` 欄位），但 intent 連「取消是否該連動退款判斷」都還沒有人拍板。也就是說，spec 已經替尚未確認的目的做了技術決策（RefundRequested 該在什麼條件下是 true/false），這正是 intent.md 第10行提醒的「做出功能≠改善結果」的落差本體。

**需要向人確認的問題：**
1. `RefundRequested` 該由什麼條件觸發（例如 `Paid && !Shipped` 才要退款旗標？)？這件事該誰拍板？
2. 若訂單已出貨（Shipped=true），Cancel 呼叫應該回什麼結果——直接不允許，還是回傳原狀態？spec 沒寫這個分支的期待行為。
3. 「已取消（Cancelled=true）的訂單」再次呼叫 Cancel，期待行為是什麼？

這三點目前在 spec.md 裡完全沒規範，而 intent.md 也還沒確認owner，建議先請需求負責人補上這些情境的期待行為，再往下實作。