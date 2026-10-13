# p-l01-007-sink-connect-timeout|縮短 NotificationWorker 對接收端的連線逾時，讓死信在驗收等待窗（8 秒）內寫入清單

【目標】
只改 order-service/src/Api/Program.cs（不碰 acceptance/ 與 LOCK.json 鎖定檔）：1) 新增環境變數 OC_SINK_CONNECT_TIMEOUT_MS，預設 500，讀不到或不合法就用 500。2) 讓 NotificationWorker 的 `_http` 與 SendOnce 的 `SharedHttp` 都改成 `new HttpClient(new SocketsHttpHandler { ConnectTimeout = TimeSpan.FromMilliseconds(x) })`，另設合理的整體 Timeout（例如 5 秒），避免接收端半死時卡住 worker。3) 不改 Backoff 陣列與重試次數（仍為 200/400/800ms，共 4 次嘗試）。4) 逾時當作一般失敗處理：lastError 沿用 `e.GetType().Name`（TaskCanceledException 或 HttpRequestException），照舊 log notify_attempt_failed 並進入下一次重試。5) 在 ld/ 分支上先實測「接收端掛掉時，cancel 到死信出現」的耗時，要求小於 6 秒，並把數字寫進 PR 描述。風險備註：500ms 對本機／同機房接收端足夠；若接收端是遠端，可透過環境變數調大，預設值不影響既有 DomainTests。

【約束】
- 本卡由 loop engineer `l-01-notify-retry` 於 2026-10-11 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：AT-12（不退步守門）必須保持綠燈（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. 接收端掛掉時，從 POST /orders/{id}/cancel 到 GET /admin/dead-letters 列出該筆的耗時小於 6 秒，實測數字附在 PR 描述。
2. `python order-service/acceptance/run_acceptance.py` 中 AT-01 轉綠，且 AT-03/04/07/08/11 不再因「沒進死信」而失敗，預期轉綠或推進的 AT：AT-01、AT-03、AT-04、AT-07、AT-08、AT-11。AT-05 另需自動重送提案（p-l01-003），不在本卡範圍。
3. AT-02 與 AT-12 保持綠燈，既有 DomainTests 全過。
4. git diff 只含 order-service/src/Api/Program.cs，acceptance/ 與 LOCK.json 雜湊不變。
5. 未設 OC_SINK_CONNECT_TIMEOUT_MS 時預設 500ms；設為非數字或 0 以下時回到預設值，且服務照常啟動。

【證據】
觀測到的差距：p-l01-001 的死信清單程式已經合進 main（Program.cs 的 DeadLetterStore、/admin/dead-letters、兩處 dl.Add 都在），但驗收仍是 2/12（AT-02、AT-12 綠）。AT-01 與其他「沒進死信」的條件（AT-03/04/05/07/08/11）仍然紅燈。原因不是邏輯缺漏，而是時間：接收端掛掉時，每次 POST 被拒連線要約 2.2 秒才失敗，4 次嘗試加上 200/400/800ms 的 backoff 約 11 秒，才呼叫 dl.Add。驗收的 wait_until 只等 8 秒，所以永遠等不到死信。這個瓶頸擋住 7 條 AT，比 002～006 任何一張的覆蓋面都大，而且目前沒有提案處理它。

SSOT：`order-service/acceptance（run_acceptance.py 結果）`

- 實跑 `python order-service/acceptance/run_acceptance.py`：AT-01 fail「死信清單沒有這筆通知」；AT-03/04/05/07/08/11 fail「沒進死信」；合計 2/12 pass。單跑 AT-01 結果相同。
- order-service/acceptance/run_acceptance.py:115-116：at01 只呼叫 `wait_until(lambda: e.dl_for(oid), 8)`，等待上限 8 秒，且該情境沒有啟動 sink。
- order-service/acceptance/.run/at01/logs.jsonl：cancel 於 10:42:44.41，`notify_attempt_failed` attempt 0/1/2 分別在 10:42:46.50、10:42:48.76、10:42:51.22。每次失敗間隔約 2.2～2.5 秒，其中 backoff 只佔 0.2～0.8 秒。第 4 次嘗試與 dl.Add 要到約 10:42:55 之後才發生，已超過 8 秒窗。
- order-service/src/Api/Program.cs:118、132-136、281、330：/admin/dead-letters、DeadLetterStore.Add、worker 與 SendOnce 兩處 dl.Add 都已存在。程式路徑正確，只是太晚執行。
- order-service/src/Api/Program.cs:258 與 267：worker 用的 `_http = new()` 和 SendOnce 用的 `SharedHttp = new()` 都沒設 ConnectTimeout／Timeout，被拒連線的等待時間完全由作業系統決定。
- order-service/acceptance/SPEC.md 背景段：現況是「重試 3 次（200／400／800 ms）」，沒有要求更改 backoff。因此該調的是連線逾時，不是 backoff。
