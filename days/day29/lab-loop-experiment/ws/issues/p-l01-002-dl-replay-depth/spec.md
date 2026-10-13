# p-l01-002-dl-replay-depth|新增死信手動重送端點 POST /admin/dead-letters/{id}/replay 與 oc_notify_dead_letter_depth 指標

【目標】
前置條件是 dead-letter-list 提案已合併。1) 在 DeadLetterStore 增加 TryGetPending 與 MarkDelivered。2) 新增 app.MapPost("/admin/dead-letters/{id}/replay")，沿用 /admin/* 的 X-Actor 檢查：找不到或已 delivered 回 404；對 sink 單次 POST，成功就 MarkDelivered、遞增 notify_sent_total 並寫 notify_sent log（含 replay=true）後回 200，失敗則維持 pending 並回 502。replay 要有針對同一 id 的互斥（lock 或 per-id semaphore），避免並發重複送出。3) 在 /metrics 輸出處（Program.cs:144 附近）新增 oc_notify_dead_letter_depth，值為 store 中 status==pending 的筆數。

【約束】
- 本卡由 loop engineer `l-01-notify-retry` 於 2026-10-04 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：AT-12（不退步守門）必須保持綠燈（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. python acceptance/run_acceptance.py 輸出中 AT-03、AT-04、AT-07 為 pass（AT-01、AT-02 維持 pass）
2. AT-12 仍為 pass，acceptance/ 與 LOCK.json 雜湊不變
3. 並發對同一 notification_id 呼叫兩次 replay，FakeSink 收據只有一筆
4. 整體得分提升到至少 6/12 pass（AT-01、02、03、04、07、08 加上 AT-12）

【證據】
觀測到的差距：在死信清單存在之後，下一步是補上手動重送，並讓重送冪等；同時把待重送筆數以指標形式暴露。這三項各對應一個 AT，且彼此只依賴死信清單，不依賴自動重送或持久化，適合排在第二輪。

SSOT：`order-service/acceptance（run_acceptance.py 結果）`

- order-service/acceptance/SPEC.md AT-03：replay 在接收端恢復時回 200，接收端收到收據，死信清單不再列出
- order-service/acceptance/SPEC.md AT-04：已送達的通知再 replay 回 404 或 409，接收端收據仍只有一筆
- order-service/acceptance/SPEC.md AT-07：/metrics 要有 oc_notify_dead_letter_depth，等於待重送筆數，送達後歸零
- order-service/src/Api/Program.cs:144 目前只輸出 oc_notify_queue_depth，沒有 dead_letter_depth；run_acceptance.py 目前輸出 AT-03/04/07 fail「沒進死信」
