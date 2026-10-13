# p-l02-003-spike-for-duration|HighLatency／QueueBacklog 加 for_minutes，AnyServerError 單點錯誤改 ticket

【目標】
HighLatency：for_minutes=5，保留 threshold=150，26 分鐘的真實事故仍會觸發。QueueBacklog：for_minutes=5。AnyServerError：先維持 page 但 for_minutes=3，同時新增一條 ticket 規則 AnyServerErrorTicket（error_rate>0、for_minutes=0、severity=ticket），讓單點錯誤仍留痕。注意：只有一天資料，AnyServerError 是否為事故訊號尚無法驗證，所以採「降級加留痕」而不是刪除。

【約束】
- 本卡由 loop engineer `l-02-alert-tuning` 於 2026-10-04 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：不得修改 ops/data/、ops/scores/（外層寫入）；不得嘗試取得出題程式或事故答案（Stability_Goals 煞車）
- 不得破壞護欄：不得用關掉告警或放寬到永不觸發降雜訊；漏報一律算失敗（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. HighLatency、QueueBacklog 的 for_minutes=5，AnyServerError 的 for_minutes=3，並新增 ticket 級留痕規則
2. 以 day01 離線推演：HighLatency 在第 1241 分鐘事故窗仍會觸發 1 次，其餘 34 段短尖峰不觸發
3. 次日成績單 missed 不新增，page_noise 進一步下降
4. 沒有任何規則被關閉或放寬到永不觸發
5. 未修改 ops/data/、ops/scores/、acceptance/、LOCK.json

【證據】
觀測到的差距：剩下的 page 規則被短暫尖峰觸發，共 80 次雜訊，但真正的延遲事故是持續性的。可用持續時間濾掉尖峰又不漏報。

SSOT：`order-service/ops（data/ 每日指標、scores/ 外層成績單、alerts/rules.yml）`

- day01.json per_rule: HighLatency fired=35 valid=1 noise=34；QueueBacklog fired=33 valid=0；AnyServerError fired=13 valid=0
- metrics.json p95_latency_ms：超過 150 共 35 段，其中 34 段不到 3 分鐘，唯一的長段是第 1241 分鐘起連續 26 分鐘、峰值 419.6，對應 valid=1
- metrics.json queue_depth：超過 8 共 33 段，全部不到 3 分鐘，峰值 29.4
- metrics.json error_rate：13 段全是單一分鐘的 1.0 孤點，無連續段
- rules.yml 目前三條規則 for_minutes 皆為 0
