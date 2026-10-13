# p-l01-004-admin-reconcile|新增 GET /admin/reconcile 對帳端點（transitions == delivered + pending + abandoned）

【目標】
前置條件是 p-l01-001（DeadLetterStore 與 /admin/* X-Actor 檢查）合併，且 abandoned 狀態已存在（見 auto-redelivery-abandon 提案）。只改 order-service/src/Api/Program.cs：新增 app.MapGet("/admin/reconcile")，沿用 /admin/* 的 X-Actor 檢查。transitions 取 transitions_total；delivered 取 notify_sent_total；pending、abandoned 取 DeadLetterStore 中對應 status 的筆數，另把仍在佇列或重試中的通知計入 pending，確保恆等式成立。回傳 JSON {transitions, delivered, pending, abandoned}。

【約束】
- 本卡由 loop engineer `l-01-notify-retry` 於 2026-10-05 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：AT-12（不退步守門）必須保持綠燈（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. python acceptance/run_acceptance.py 輸出 AT-09 為 pass
2. 多筆取消、混合送達／死信／放棄後，transitions == delivered + pending + abandoned 恆成立
3. 沒帶 X-Actor 回 401，且 AT-02 維持 pass
4. AT-12 仍為 pass，acceptance/ 與 LOCK.json 雜湊不變
5. 預期轉綠 AT：AT-09

【證據】
觀測到的差距：SPEC 要求有對帳端點讓人確認每一筆狀態轉換最終都有去處，但目前完全沒有 /admin/ 路由，AT-09 紅燈。transitions_total 計數器已存在，只缺 delivered/pending/abandoned 的彙總。

SSOT：`order-service/acceptance（run_acceptance.py 結果）`

- order-service/acceptance/SPEC.md AT-09：GET /admin/reconcile 回 transitions、delivered、pending、abandoned，且 transitions == delivered + pending + abandoned
- order-service/src/Api/Program.cs:92：取消成功時 metrics.Inc("transitions_total")，94 行同時 Inc notify_enqueued_total 並入佇列，可作為 transitions 來源
- order-service/src/Api/Program.cs 全檔 grep "admin" 無命中，目前沒有 /admin/reconcile
- issues/p-l01-001-dead-letter-list/spec.md 證據：run_acceptance.py 輸出 AT-06/09/10 fail「/admin/dead-letters 回 404」，整體 1/12 pass
