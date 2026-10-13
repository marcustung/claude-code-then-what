# p-l01-005-manual-followup-flag|通知被放棄且訂單已付款時，GET /orders/{id} 回 needs_manual_followup: true（補償旗標）

【目標】
前置條件是 abandoned 狀態已存在（auto-redelivery-abandon 提案）。只改 order-service/src/Api/Program.cs：在通知轉為 abandoned 的同一處，若 Notification.RefundRequested==true，就把該 order_id 加入 ConcurrentDictionary 型別的 FollowupSet；GET /orders/{id} 的回應 JSON 增加 needs_manual_followup 欄位（在 FollowupSet 內為 true，否則 false）。未付款或不需退款的訂單即使通知被放棄也不得設旗標。不改變既有欄位。

【約束】
- 本卡由 loop engineer `l-01-notify-retry` 於 2026-10-05 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：AT-12（不退步守門）必須保持綠燈（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. python acceptance/run_acceptance.py 輸出 AT-10 為 pass
2. 未付款訂單的通知被放棄時，needs_manual_followup 為 false
3. 既有 GET /orders/{id} 欄位不變，AT-12 與 dotnet run --project tests/DomainTests 全過
4. acceptance/ 與 LOCK.json 雜湊不變
5. 預期轉綠 AT：AT-10

【證據】
觀測到的差距：已付款訂單取消會退款，若退款通知最終被放棄，現況沒有任何訊號讓人工接手，AT-10 紅燈。

SSOT：`order-service/acceptance（run_acceptance.py 結果）`

- order-service/acceptance/SPEC.md AT-10：已付款（會退款）的訂單，通知被放棄時，GET /orders/{id} 回 needs_manual_followup: true
- order-service/src/Api/Program.cs:44：建單時記錄 paid；93 行 Notification 帶 RefundRequested（取消時由 result.RefundRequested 決定），可判斷該通知是否屬於退款
- order-service/src/Api/Program.cs 全檔 grep needs_manual 無命中
- issues/p-l01-001-dead-letter-list/spec.md 證據：run_acceptance.py 目前輸出 AT-10 fail
