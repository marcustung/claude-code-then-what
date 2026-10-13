# p-l01-001-dead-letter-list|在 NotificationWorker 加入記憶體死信清單與受 X-Actor 保護的 GET /admin/dead-letters

【目標】
只改 order-service/src/Api/Program.cs（不碰 acceptance/ 與 LOCK.json 鎖定的檔案）：1) 新增 DeadLetterStore（ConcurrentDictionary<string, DeadLetter>），DeadLetter 欄位為 notification_id、order_id、attempts、last_error、status（初始 "pending"）以及原始 Notification。2) 在 NotificationWorker 的 worker 路徑與 SendOnce 兩處，重試用盡時呼叫 store.Add，並記下最後一次失敗的 status code 或例外型別作為 last_error。3) 新增 app.MapGet("/admin/dead-letters")，只列出 status==pending 的項目。4) 為 /admin/* 加上 group 或 filter：沒有 X-Actor 一律回 401（比照 cancel 的 unauthorized JSON 格式）。5) 只改動 sent/dead_letter 路徑，不得改變 notify_sent_total 的遞增時機。AT-08 目前紅燈只是因為前置條件「沒進死信」，這個改動預期可一併讓它轉綠。

【約束】
- 本卡由 loop engineer `l-01-notify-retry` 於 2026-10-04 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：AT-12（不退步守門）必須保持綠燈（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. python acceptance/run_acceptance.py 輸出中 AT-01、AT-02 為 pass，預期 AT-08 同步轉綠
2. AT-12 仍為 pass，且 dotnet run --project tests/DomainTests 全過
3. git diff 不含 acceptance/ 下任何檔案，LOCK.json 的雜湊比對一致
4. 接收端掛掉時，死信項目的 attempts 等於 4（Backoff.Length + 1），last_error 非空

【證據】
觀測到的差距：目前 AT-01～AT-11 全部紅燈，只有 AT-12 綠燈（1/12 pass），離目標 ≥ 7/11 差 7 項。多數 AT 失敗的共同根因是重試用盡後只遞增計數器並寫 notify_dead_letter log，沒有任何可查的死信資料結構，也沒有 /admin/* 路由。這是所有後續 AT（重送、放棄、對帳、補償、持久化）的前置步驟。

SSOT：`order-service/acceptance（run_acceptance.py 結果）`

- 執行 python order-service/acceptance/run_acceptance.py 的實際輸出：AT-01 fail「死信清單沒有這筆通知」、AT-02 fail「沒帶 X-Actor 也能存取」、AT-03/04/05/07/08/11 fail「沒進死信」、AT-06/09/10 fail「/admin/dead-letters 回 404」、AT-12 pass，合計 1/12 pass
- order-service/src/Api/Program.cs:253-258 與 304-305：重試用盡後只做 m.Inc("notify_failed_total")、m.Inc("notify_dead_letter_total") 與 log.Write(notify_dead_letter)，沒有保存 notification 內容與 last_error
- order-service/src/Api/Program.cs 全檔沒有 /admin/ 路由（grep "admin" 無命中）；X-Actor 檢查目前只存在於 POST /orders/{id}/cancel（Program.cs:57-62）
- order-service/acceptance/SPEC.md AT-01：GET /admin/dead-letters 須列出 notification_id、order_id、attempts、last_error、status；AT-02：/admin/* 沒有 X-Actor 要回 401
