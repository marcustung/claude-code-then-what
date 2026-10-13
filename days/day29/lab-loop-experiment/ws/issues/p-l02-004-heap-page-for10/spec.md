# p-l02-004-heap-page-for10|HeapHigh 改為「page 級、for_minutes=10」，不要降成 ticket（修正 p-l02-002 對 HeapHigh 的做法）

【目標】
在 p-l02-002 裁決時，把 HeapHigh 的處理方式換掉（或另開一張取代它）。HeapHigh 保留 severity=page，threshold 維持 120，只把 for_minutes 設為 10。鋸齒每次只持續 6 分鐘，不會連續 10 分鐘超過 120，所以不會觸發。day02 的洩漏連續約 111 分鐘，約在第 311 分鐘即觸發 page。ManyConflicts 降為 ticket、for_minutes=5 的部分不受影響，維持 p-l02-002 的原案。不要把 threshold 拉到 130 以上，因為鋸齒峰值 128.38，邊際只有 1.6，很脆弱。

【約束】
- 本卡由 loop engineer `l-02-alert-tuning` 於 2026-10-05 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：不得修改 ops/data/、ops/scores/（外層寫入）；不得嘗試取得出題程式或事故答案（Stability_Goals 煞車）
- 不得破壞護欄：不得用關掉告警或放寬到永不觸發降雜訊；漏報一律算失敗（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. rules.yml 的 HeapHigh 為 severity=page、for_minutes=10、threshold<=120，且規則沒有被刪除或停用。
2. 以 day01 與 day02 的 heap_mb 離線推演：鋸齒（每次 6 分鐘）觸發 0 次；day02 第 301~409 分鐘的洩漏至少觸發 1 次 page，約在第 311 分鐘。
3. 次日成績單 HeapHigh 的 valid>=1 且 noise 相對 day02 的 35 大幅下降；missed 不新增任何事故種類。
4. 未修改 ops/data/、ops/scores/、acceptance/、LOCK.json。

【證據】
觀測到的差距：day02 出現真實的 heap 洩漏事故，推翻了 p-l02-002 的前提。該提案以 day01 為依據，把 HeapHigh 當成零 valid 的純雜訊，要降成 ticket。day02 的 HeapHigh 卻有 valid=2，metrics.json 也看得到一段連續 111 分鐘的爬升。HeapHigh 若降成 ticket，真實洩漏就只剩工單，不會通知人，等於降低該事故的偵測等級。目前 page 雜訊仍是 392/日（day01 為 397），離「降 30%」的目標還有距離。HeapHigh 每天 37~39 次的鋸齒雜訊可以靠持續時間濾掉，不必降級。

SSOT：`order-service/ops（data/ 每日指標、scores/ 外層成績單、alerts/rules.yml）`

- order-service/ops/scores/day02.json per_rule: HeapHigh fired=37 valid=2 noise=35；day01.json 同規則 fired=39 valid=0 noise=39。valid 從 0 變 2，代表 heap 事故是真的。
- order-service/ops/data/day02/metrics.json heap_mb：第 301~409 分鐘連續超過 120（共 109 點超過 130，起點約 143.6，峰值 434.82），是持續約 111 分鐘的洩漏爬升。鋸齒則維持每次 6 分鐘、峰值 128.38（第 31、68、105、142… 分鐘開始，day01 與 day02 相同）。
- order-service/ops/data/day01/metrics.json heap_mb：最長連續超過 120 為 6 分鐘、峰值 128.38，全是鋸齒，沒有洩漏。
- ws/issues/p-l02-002-conflict-heap-ticket/spec.md：HeapHigh 提議改 severity=ticket、for_minutes=10，依據是「零 valid、鋸齒不是洩漏」，只看過 day01。
- order-service/ops/alerts/rules.yml HeapHigh: threshold=120, for_minutes=0, severity=page。
