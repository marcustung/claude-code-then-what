# p-l02-005-silent-drop-day02-recheck|p-l02-001 的 silent_drop 規則在 day02 再度驗證：事故窗位置不固定，規則不得綁定時段

【目標】
不另開新規則。請裁決者核准 p-l02-001。day02 的資料同樣符合它的設計：threshold=10、for_minutes=2 的條件在 day02 約第 566 分鐘觸發，窗外 0 次。落地前的離線推演驗收，請同時涵蓋 day01 與 day02 兩天。

【約束】
- 本卡由 loop engineer `l-02-alert-tuning` 於 2026-10-05 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：不得修改 ops/data/、ops/scores/（外層寫入）；不得嘗試取得出題程式或事故答案（Stability_Goals 煞車）
- 不得破壞護欄：不得用關掉告警或放寬到永不觸發降雜訊；漏報一律算失敗（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. p-l02-001 的離線推演同時用 day01、day02 的 receipts_gap：兩天事故窗（day01 第 1157~1222、day02 第 564~616 分鐘）都觸發，窗外各 0 次。
2. 次日成績單 missed 不再含 silent_drop。
3. 未修改 ops/data/、ops/scores/、acceptance/、LOCK.json。

【證據】
觀測到的差距：day02 成績單 missed 仍是 silent_drop，漏報已連續兩天出現，而 rules.yml 仍沒有 receipts_gap 規則。p-l02-001 目前還在 review 沒有合併。day02 的資料帶來新證據：事故窗從 day01 的第 1155~1223 分鐘移到 day02 的第 562~617 分鐘，所以規則必須用持續性條件偵測，不能用時間窗。這輪沒有開新提案，只補證據，讓裁決者能放心核准 p-l02-001。

SSOT：`order-service/ops（data/ 每日指標、scores/ 外層成績單、alerts/rules.yml）`

- order-service/ops/scores/day02.json: "missed": ["silent_drop"]，incidents=3；day01.json 同樣 missed=[silent_drop]，連續兩天漏報。
- order-service/ops/data/day02/metrics.json receipts_gap：唯一一段非零是第 562~617 分鐘（56 點），超過 10 的連續段為第 564~616 分鐘（53 分鐘），峰值 92.1，其餘時間皆為 0。
- order-service/ops/data/day01/metrics.json receipts_gap：非零段第 1155~1223 分鐘（69 點），超過 10 的連續段第 1157~1222 分鐘（66 分鐘），峰值 125.1。
- order-service/ops/alerts/rules.yml：5 條規則，沒有 receipts_gap。
- ws/issues/p-l02-001-silent-drop-rule/spec.md：提議 receipts_gap>10、for_minutes=2、severity=page，目前 state=review。
