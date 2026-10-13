# p-l02-002-conflict-heap-ticket|ManyConflicts、HeapHigh 降為 ticket 並加持續時間（零 valid、共 317 次 page 雜訊）

【目標】
ManyConflicts：severity 改 ticket，for_minutes=5，threshold 維持 3（不放寬到永不觸發，仍可留痕）。HeapHigh：severity 改 ticket，for_minutes=10（鋸齒單次只持續 6 分鐘，真正的洩漏會持續超過 10 分鐘）。兩條規則都保留、不刪除，維持可見性。

【約束】
- 本卡由 loop engineer `l-02-alert-tuning` 於 2026-10-04 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：不得修改 ops/data/、ops/scores/（外層寫入）；不得嘗試取得出題程式或事故答案（Stability_Goals 煞車）
- 不得破壞護欄：不得用關掉告警或放寬到永不觸發降雜訊；漏報一律算失敗（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. 兩條規則 severity=ticket，for_minutes 分別為 5、10，threshold 不變或更嚴
2. 次日成績單這兩條規則的 page 觸發數為 0，ticket_noise 可 >0
3. page_noise 相對 day01 的 397 下降 ≥30%（預期約 -317）
4. missed 不新增任何事故種類
5. 未修改 ops/data/、ops/scores/、acceptance/、LOCK.json

【證據】
觀測到的差距：兩條規則在 day01 的 page 觸發全是雜訊，占 page 雜訊 397 的 80%，是達成「雜訊下降 ≥30%」的最大單一來源。

SSOT：`order-service/ops（data/ 每日指標、scores/ 外層成績單、alerts/rules.yml）`

- order-service/ops/scores/day01.json per_rule: ManyConflicts fired=278 valid=0 noise=278；HeapHigh fired=39 valid=0 noise=39；page_noise=397
- metrics.json http_409_rate：p50=2.08，p90=4.28，超過門檻 3 的 278 段中 251 段不到 3 分鐘，最長僅 5 分鐘，屬正常抖動
- metrics.json heap_mb：每約 37 分鐘一次、每次 6 分鐘的規律鋸齒，峰值固定 128.38（第 31、68、105、142… 分鐘開始），是週期性 GC 行為，不是洩漏；p50=99.19
