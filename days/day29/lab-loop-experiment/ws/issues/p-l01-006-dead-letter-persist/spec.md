# p-l01-006-dead-letter-persist|死信持久化到 OC_RUN_DIR（JSON lines），服務重啟後還原死信清單

【目標】
前置條件是 p-l01-001 已合併。只改 order-service/src/Api/Program.cs：DeadLetterStore 每次 Add／狀態變更（delivered、abandoned、rounds）時，以 lock 內寫入 {runDir}/dead-letters.jsonl（先寫暫存檔再 File.Move 覆蓋以確保原子性，整份快照式重寫即可，量小）。啟動時若檔案存在就載入還原；損毀行跳過並寫 WARN log，不得讓服務啟動失敗。Notification 原始內容要一併存下，重啟後才能重送。

【約束】
- 本卡由 loop engineer `l-01-notify-retry` 於 2026-10-05 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：AT-12（不退步守門）必須保持綠燈（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. python acceptance/run_acceptance.py 輸出 AT-11 為 pass
2. 死信產生後重啟服務，GET /admin/dead-letters 仍列出相同筆數與欄位，且重啟後 replay 仍可成功
3. dead-letters.jsonl 含損毀行時服務仍可啟動
4. AT-12 仍為 pass，acceptance/ 與 LOCK.json 雜湊不變
5. 預期轉綠 AT：AT-11

【證據】
觀測到的差距：p-l01-001 規劃的 DeadLetterStore 是純記憶體，服務一重啟死信全部遺失，AT-11 無法轉綠。SPEC 明確要求持久化。

SSOT：`order-service/acceptance（run_acceptance.py 結果）`

- order-service/acceptance/SPEC.md AT-11：死信要持久化，存在 OC_RUN_DIR 下，服務重啟後死信清單仍在
- order-service/src/Api/Program.cs:10：runDir 已由 OC_RUN_DIR 環境變數取得（預設 runs/default），可直接放檔案
- issues/p-l01-001-dead-letter-list/spec.md【目標】明訂 DeadLetterStore 為 ConcurrentDictionary 記憶體結構，並未持久化；該卡驗收也不含 AT-11
- SSOT 現況：run_acceptance.py 輸出 AT-11 fail「沒進死信」，整體 1/12 pass
