# p-l02-006-conflicts-page-for10|ManyConflicts 維持 page 級，只加 for_minutes=10 濾掉短暫 409 尖峰（承接被退回的 p-l02-002 中 ManyConflicts 的部分）

【目標】
只改 order-service/ops/alerts/rules.yml 的 ManyConflicts 一條：threshold 維持 3，severity 維持 page，for_minutes 從 0 改為 10。不要把 threshold 拉高，也不要降成 ticket。for_minutes 取 10 而非 5 的理由：day01 有 5 分鐘連續段，取 5 仍會殘留 5 次雜訊；三天最長 5 分鐘，取 10 有一倍的餘裕。若持續性的 409 風暴成為真實事故，仍會在 10 分鐘後 page。三天都沒有 valid，無法證明 409 事故存在，所以不採刪除或降級。與 p-l02-001／003／004 改的是不同規則，可獨立合併。

【約束】
- 本卡由 loop engineer `l-02-alert-tuning` 於 2026-10-06 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：不得修改 ops/data/、ops/scores/（外層寫入）；不得嘗試取得出題程式或事故答案（Stability_Goals 煞車）
- 不得破壞護欄：不得用關掉告警或放寬到永不觸發降雜訊；漏報一律算失敗（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. rules.yml 的 ManyConflicts 為 severity=page、threshold=3（不高於現值）、for_minutes=10，規則沒有被刪除或停用，其他規則一律不動。
2. 以 day01~day03 的 http_409_rate 離線推演：for_minutes=10 時三天觸發次數皆為 0；並說明若出現連續 ≥10 分鐘超過 3 的段落就會觸發 page。
3. 次日成績單 ManyConflicts 的 noise 相對 day01~03 的 278／285／279 下降 ≥90%，page_noise 相對 day03 的 395 下降 ≥30%（假設 p-l02-003、004 一併合併），且 missed 不新增任何事故種類。
4. 未修改 ops/data/、ops/scores/、acceptance/、LOCK.json。

【證據】
觀測到的差距：ManyConflicts 每天 278–285 次 page，三天 valid 全為 0，佔每日 page 雜訊（約 392–397）的約 71%。已核准的 p-l02-001/003/004 分別處理 silent_drop、HighLatency／QueueBacklog／AnyServerError、HeapHigh，沒有任何一張涵蓋 ManyConflicts。p-l02-002 是唯一處理它的提案，但已因「方向不對」被退回（把它降成 ticket）。就算前三張全部落地，每日 page 雜訊仍約 280，達不到「下降 ≥30%」。本案不降級，保留 page 並只加持續時間，符合 l-02 的設計準則：降雜訊只用 for_minutes，不降 severity。

SSOT：`order-service/ops（data/ 每日指標、scores/ 外層成績單、alerts/rules.yml）`

- order-service/ops/scores/day01.json per_rule: ManyConflicts fired=278 valid=0 noise=278（page_noise=397）；day02.json: fired=285 valid=0（page_noise=392）；day03.json: fired=279 valid=0（page_noise=395）
- order-service/ops/alerts/rules.yml: ManyConflicts metric=http_409_rate, op='>', threshold=3, for_minutes=0, severity=page。這是五條規則中唯一一條沒有任何已核准提案處理的雜訊規則。
- order-service/ops/data/day01~03/metrics.json http_409_rate（我用腳本離線重算）：超過 3 的連續段分別為 278／285／279 段，最長連續只有 5／4／4 分鐘，峰值 13.47／14.3／13.58。以 threshold=3 計，for_minutes=3 仍觸發 27／16／15 次，for_minutes=5 在 day01 仍觸發 5 次，for_minutes=10 三天各 0 次。
- ws/issues/p-l02-002-conflict-heap-ticket/spec.md：ManyConflicts 提議改 severity=ticket、for_minutes=5，裁決為 rejected（方向不對）。本案與它的差異：severity 不降，for_minutes 取 10 以使三天的雜訊歸零，且 threshold 不動。
- ws/issues/l-02-alert-tuning/runs/2026-10-05-run1.md 的 DERIVED 分類理由：降雜訊時不要把規則降為 ticket，只用 for_minutes 濾掉短暫尖峰。
