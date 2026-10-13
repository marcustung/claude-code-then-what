# p-l03-001-receipt-time-check|Skill 加入「收據時間須晚於發送事件」的時序一致性查核，修正 h3 語意 0/2

【目標】
只改 skill-lab/skill/.claude/skills/trace-notification/ 底下的檔案，分三點：
1. collect.py：在 sender record 加 `ts`（取自 log 的 ts，轉成 epoch 秒）。在 receiver record 加 `at`（取自 receipts.json 的 at）。另給每筆 receiver record 加 `time_order`，值為 `after_sent`、`before_sent` 或 `no_sender`，由 receipt.at 與同 notification_id 的 notify_sent.ts 比出。比較時容許 ±2 秒時鐘偏差。
2. SKILL.md「查核迴圈」新增一步：接收端收據的時間若早於同一通知的 notify_sent（`time_order=before_sent`）、或早於該通知的 cancel 事件，視為證據自相矛盾。此時 receiver_status 填 unknown，missing_sources 寫「時序可信的接收端收據」，next_action 寫明請人核對時鐘與收據來源。
3. CHANGELOG 與 VERSION 升到 2.2.0，並在 SKILL.md 版本段記一行。
不得動 check_result.py、gate.py、cases/、expected.json、eval.py。提案分支驗證時只可執行 selftest.py，不得執行 eval.py，語意成績以隔日外層 Eval 為準。

【約束】
- 本卡由 loop engineer `l-03-skill-opt` 於 2026-10-04 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：只改 skill-lab/skill/；不得修改 cases/、expected.json、eval.py、eval/gate/（Stability_Goals 煞車）
- 不得破壞護欄：不得自己執行 skill-lab/eval.py（外層每天 01:50 在 main 上跑一次，成績寫進 skill-lab/scores/）；以成績單判斷，有退步不得送審（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. diff 只出現在 skill-lab/skill/ 之下；cases/、expected.json、eval.py、eval/gate/、acceptance/、LOCK.json 的雜湊與 main 一致
2. 以 h3 的 data 跑 collect.py，receiver record 的 time_order 為 before_sent；以 complete、h1、h4 的 data 跑，time_order 為 after_sent
3. selftest.py 退出碼 0
4. 隔日外層 Eval 成績單中 h3 語意 ≥1/2，且其餘 8 個案例的 semantic 都不低於 day01（complete 2、decoy-receipt 2、h1 2、h2 2、h4 2、h5 2、h6 1、missing-receipts 2），總語意 ≥16/18
5. 成績單任何案例相對 day01 退步時不得送審

【證據】
觀測到的差距：最新成績單中 h3-receipt-before-cancel 語意正確 0/2，是 18 次中最大的單點失分，也是 15/18 基準偏低的主因之一。這個案例的收據 `at` 早於 log 裡的 cancel 與 notify_sent 時間，證據自相矛盾，正解是 receiver_status=unknown。SKILL.md 的查核迴圈沒有要求比對時間先後。collect.py 的 records 也不帶時間欄位，模型只看到 receipt:0 與 notification_id 吻合，就判成 confirmed。

SSOT：`order-service/skill-lab（scores/ 外層每日 Eval 成績單、skill/）`

- order-service/skill-lab/scores/day01.json：per_case.h3-receipt-before-cancel = {semantic:0, contract:2, runs:2}；semantic_ok=15/runs=18
- order-service/skill-lab/expected.json：h3-receipt-before-cancel → receiver_status=unknown，why=「收據時間早於取消事件，證據自相矛盾，不能採信」
- order-service/skill-lab/cases/h3-receipt-before-cancel/data/receipts.json：at=1790642410.857…；同目錄 logs.jsonl 的 notify_sent ts=2026-09-29T09:40:10.861+08:00。h6 案例同一筆收據的 at 是 1790646010.857…，與 h3 差整整 3600 秒，可見 h3 的收據被提前了一小時。
- order-service/skill-lab/skill/.claude/skills/trace-notification/SKILL.md「查核迴圈」第 4、5 步：只要求分開 API／發送端／接收端，以及缺證據標 unknown，沒有任何時序比對要求
- order-service/skill-lab/skill/.claude/skills/trace-notification/scripts/collect.py：records 的欄位只有 ref/side/event/order_id/notification_id/version/source，不含 receipt 的 at 或 log 的 ts
