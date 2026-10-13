# p-l01-003-auto-redelivery-abandon|新增死信自動重送背景迴圈與 abandoned 放棄狀態（OC_REDELIVERY_INTERVAL_MS / MAX_ROUNDS）

【目標】
前置條件是 p-l01-001 已合併（需要 DeadLetterStore）。只改 order-service/src/Api/Program.cs：1) DeadLetter 增加 rounds 欄位，status 增加 abandoned。2) 新增 BackgroundService，每 OC_REDELIVERY_INTERVAL_MS 掃描 status==pending 的死信，對 sink 單次 POST。成功就標記 delivered 並遞增 notify_sent_total、寫 notify_sent log，失敗就 rounds+1。3) rounds 達 OC_REDELIVERY_MAX_ROUNDS 仍失敗時，狀態改為 abandoned，m.Inc("notify_abandoned_total")，並寫 level=ERROR、event=notify_abandoned 的 log。4) /metrics 輸出 oc_notify_abandoned_total。5) 與手動 replay 共用 per-id 互斥（沿用 p-l01-002 的鎖），避免重複送出。6) 兩個環境變數缺省時用安全預設值（例如 5000ms／5 輪）。

【約束】
- 本卡由 loop engineer `l-01-notify-retry` 於 2026-10-05 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：AT-12（不退步守門）必須保持綠燈（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. python acceptance/run_acceptance.py 輸出 AT-05、AT-06 為 pass
2. 接收端恢復後，死信在 INTERVAL × MAX_ROUNDS 內自動送達，且 FakeSink 收據只有一筆（與手動 replay 並發也不重複）
3. AT-12 仍為 pass，dotnet run --project tests/DomainTests 全過
4. git diff 不含 acceptance/ 下任何檔案，LOCK.json 雜湊一致
5. 預期轉綠 AT：AT-05、AT-06；累計（前置提案 + 本案）預期達 8/12 pass

【證據】
觀測到的差距：目前 SSOT 仍為 1/12 pass（只有 AT-12 綠），離 ≥7/11 的目標差 7 項。review 中的 p-l01-001（死信清單）與 p-l01-002（手動 replay、depth 指標）都沒有涵蓋 AT-05（自動重送）與 AT-06（放棄）。程式碼也完全沒有自動重送與 abandoned 狀態，死信一旦產生就只能靠人手動處理。

SSOT：`order-service/acceptance（run_acceptance.py 結果）`

- order-service/acceptance/SPEC.md AT-05：接收端恢復後，死信須在 INTERVAL × MAX_ROUNDS 內自動送達；AT-06：輪數用盡仍失敗則狀態改為 abandoned，oc_notify_abandoned_total 遞增，並寫 notify_abandoned 的 ERROR log
- order-service/acceptance/SPEC.md 設定表：OC_REDELIVERY_INTERVAL_MS（測試值 1000）、OC_REDELIVERY_MAX_ROUNDS（測試值 3）
- order-service/src/Api/Program.cs：全檔 grep REDELIVERY、abandoned 無命中；重試用盡只在 257 行與 304-305 行遞增 notify_failed_total / notify_dead_letter_total 並寫 notify_dead_letter log
- issues/p-l01-001-dead-letter-list/spec.md 與 issues/p-l01-002-dl-replay-depth/spec.md 的【驗收】只列 AT-01/02/03/04/07/08，沒有 AT-05、AT-06
- SSOT 現況（沿用 p-l01-001 證據）：run_acceptance.py 為 1/12 pass，兩張前置提案仍為 state=review，尚未合併
