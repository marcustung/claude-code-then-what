# 回答

## 1. 沿設計路徑走到哪一段就停了

failure-detected 是訂單 `during-update` 的取消（notification_id `d0e39019500e489cb21d391c3f303b05`）。追蹤它實際走過的步驟：

- 呼叫 Domain：`src/Program.cs:64`（`store.TryCancel`）→ `src/Cancellation.cs:19-21`
- 建通知：`src/Program.cs:82`
- 入列：`src/Program.cs:88`（走非同步 channel，非 sync_notify 分支）
- 寫日誌：`src/Program.cs:92` → 對應 `runs/acceptance-rollback-01/updated/logs.jsonl:2`（`result:"ok"`, `transitioned:true`）
- 回應：`src/Program.cs:93` → 對應 `requests.json` 中 `/orders/during-update/cancel` 回應 200、`ok:true`

**這五步全部成功跑完，API 已正常回應。** 真正卡住的地方在這條「呼叫路徑」之外：回應之後由背景的 `NotificationWorker.ExecuteAsync`（`src/Program.cs:241-256`）獨立嘗試送達，4 次嘗試（attempt 0-3，backoff 200/400/800ms，見 `Program.cs:203`）全部收到接收端 503（`updated/logs.jsonl:3-6`），超過重試次數後在 `src/Program.cs:264-265` 進入 `notify_dead_letter`（`updated/logs.jsonl:7`；對應 `report.json` 的 `failure-detected`/`failure-four-attempts`、`incident.json`）。此後沒有自動重送（`report.json`："failed-order-not-replayed": "no automatic replay"）。

**行號比對**：design-review 第 1 條寫的 69/79/84/88/89，對照目前 `src/Program.cs`：呼叫 Domain 變成第 64 行、建通知第 82 行、入列第 88 行、日誌第 92 行、回應第 93 行。整體往後挪動，原標記的第 84 行（等待入列）現在對不上（現在是第 88 行），應以目前程式行號為準。

## 2. 設計已預告、且這次撞到的條目

- **第 1 條**：「Worker 的送達與 HTTP 回應沒有固定先後」——這次正是回應先成功（`ok:true`），送達才在背景重試並最終失敗進死信，證實「回應成功不代表送達成功」。
- **第 5 條**：「持久性限制針對訂單儲存與佇列」——對應 `report.json` 的 `update-loses-memory-state`（換包後查 `before-update` 得 404）與 `rollback-does-not-restore-orders`（回復後查 `during-update` 仍 404），訂單狀態隨程序記憶體消失，與第 5 條預告一致（此為教學環境設計，非事故）。

其餘未在此次撞到（見第 3 點）。

## 3. 設計提過、但這次演練完全沒碰到

- **第 3 條**（Shipped 的 HTTP 狀態判斷 409）：整場演練所有訂單 `shipped` 均為 `false`（`before-update`、`during-update`、`after-rollback`），從未觸發已出貨拒絕分支，無任何執行證據。
- **第 4 條**（read/decide/write 非原子、並行取消安全）：`requests.json` 顯示每次都是單一序列請求，沒有並發取消，未驗證此風險。
- **第 6 條**（通知決策表 proposed vs 沿用）：這是文件層級的核對，屬於規格文字精確度問題，不是這次執行型演練能驗證的範疇，未被觸及。
- **第 2 條**（FakeSink payload 一致性）：這次雖用測試接收端記錄了 payload（`receipts.json`），但三筆成功案例的 `refund_requested` 都正確為 `true`，沒有出現 payload 被更動或遺失的情況，等於方法論有沿用、但沒有驗到第 2 條所警示的問題本身。