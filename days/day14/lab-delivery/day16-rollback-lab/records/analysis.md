## 1. 程式是否恢復？

**是，已被這次演練實際驗證。**
依據：`requests.json:116-124`(rolled-back 階段 `GET /health` 回應 `version: delivery-hardening-local-r1`，狀態 200)，以及 `rolled-back/deployment.json:2` `candidate: "candidate-checked"`（等同 before 階段的舊包），`report.json:108-114` 的 `rolled-back-version` 檢查也標記 passed。三筆一致證明程式包確實換回舊版並可回應健康檢查。

## 2. 下游（通知接收端）是否恢復？

**是，已被這次演練實際驗證。**
依據：`receipts.json:72-84`（rolled-back 階段 status 由前面連續 4 次 503 變回 `200`），對應 `rolled-back/deployment.json:15` 的 `fake_receiver_status: 200`，以及 `rolled-back/logs.jsonl:3` `notify_sent` 成功紀錄。但要注意：這只證明「接收端恢復健康」，**不能**單獨歸因於下游本身的修復——因為回復步驟是把程式與接收端一起換回（見「注意邊界」），變因未隔離，所以「下游恢復」與「程式恢復」在這次演練中是綁在一起驗證的，無法區分是哪一個動作起了作用。

## 3. 故障期間產生的資料，工作是否處理完成？

**沒有，這次沒有量測「完成」，而且從紀錄可推論「明確未完成、且不會自動完成」。**
依據：`incident.json:23` `acceptance: "service restored and unresolved order explicitly retained"`；`report.json:148-151` 的 `failed-order-not-replayed` 檢查結果是 `"no automatic replay"`；`requests.json:133-139` 顯示 rolled-back 階段查詢 `during-update` 訂單回傳 `404`（因為訂單存在程序記憶體，重啟後即消失，這是教學環境設計，不代表生產環境資料遺失）。三筆合起來說明：`during-update` 這筆訂單的取消通知在故障期間送達失敗（`receipts.json:17-70` 共 4 次 503），演練刻意不做自動重放，資料本身也因記憶體重啟而查不到，因此**沒有任何紀錄證明這筆業務事件被補償或重送完成**。

---

## 仍不能結案的工作

1. **`during-update` 這筆訂單的取消通知從未成功送達**（`notification_id: d0e39019500e489cb21d391c3f303b05`）。要處理它，需要先知道：正式環境是否有持久化訂單/通知狀態的儲存（這個教學服務用記憶體，正式環境理論上不會，但沒有紀錄證明），以及是否有獨立的補償/重放機制可依 `notification_id` 查找並重試。
2. **變因未隔離的問題**：這次「回復」把程式包和接收端同時換回，無法確認若只換回接收端、不換程式，是否也能恢復；也無法確認新程式包（r2）本身是否有問題。若要對 r2 做上線判斷，需要單獨測試「新程式包 + 健康接收端」的組合。
3. **`report.json:156` 明確寫的限制**：`in-memory state lost`、`failed business event unresolved`——這代表 `passed: true` 只代表演練把「預期會發生什麼」驗證清楚了，不是服務具備上線條件的證明。上線前仍需要正式的持久化與補償機制設計。

## 下一個該查核的項目

需要查核**是否存在（或該建立）依 `notification_id` 查找未送達通知並手動/自動補償重試的機制**——這是本次演練唯一明確標記為「未解決」且會直接影響客戶（退款通知未送達）的缺口。