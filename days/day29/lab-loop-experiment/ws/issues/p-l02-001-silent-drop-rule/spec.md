# p-l02-001-silent-drop-rule|新增 receipts_gap 持續性 page 規則，補上 silent_drop 漏報

【目標】
在 rules.yml 新增規則 SilentDropReceiptsGap：metric=receipts_gap，op='>'，threshold=10，for_minutes=2，severity=page。day01 基線全為 0，事故時第 1157 分鐘起就超過 10 並持續，所以約 2 分鐘內可觸發，且不會製造雜訊。只新增規則，不動既有規則；與其他提案互不衝突，可獨立合併。

【約束】
- 本卡由 loop engineer `l-02-alert-tuning` 於 2026-10-04 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：不得修改 ops/data/、ops/scores/（外層寫入）；不得嘗試取得出題程式或事故答案（Stability_Goals 煞車）
- 不得破壞護欄：不得用關掉告警或放寬到永不觸發降雜訊；漏報一律算失敗（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. rules.yml 新增 receipts_gap 規則，severity=page、for_minutes≥1，語法與既有規則一致
2. 以 day01 metrics 離線人工推演：事故窗 1155–1223 內會觸發，窗外 0 次觸發（即 receipts_gap 規則的 noise=0）
3. 次日成績單 missed 不再含 silent_drop
4. 未修改 ops/data/、ops/scores/、acceptance/、LOCK.json

【證據】
觀測到的差距：Evolution_Goals 要求補上 silent_drop 漏報，但 rules.yml 的 5 條規則都沒有涵蓋 receipts_gap。day01 成績單仍判 missed=[silent_drop]。漏報一律算失敗，這是最高優先的差距。

SSOT：`order-service/ops（data/ 每日指標、scores/ 外層成績單、alerts/rules.yml）`

- order-service/ops/scores/day01.json: "missed": ["silent_drop"]，incidents=2，只有 1 個事故被偵測到
- order-service/ops/alerts/rules.yml: 只有 p95_latency_ms、error_rate、http_409_rate、queue_depth、heap_mb 五個 metric，沒有 receipts_gap 或 notify_failed
- order-service/ops/data/day01/metrics.json 的 receipts_gap 序列（1440 點）：p99 才 125.1 但 99% 以上時間為 0；唯一一段非零是第 1155–1223 分鐘連續 69 分鐘，從 4.01 → 7.25 → 11.88 → 17.48 → 20.83 逐步爬升，峰值 125.1，之後回到 0。非事故時段完全沒有誤報風險
- order-service/ops/README.md: 「有 silent_drop 的日子會漏報」
