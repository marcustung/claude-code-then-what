# p-l03-002-payload-match-check|Skill 加入「收據 payload 內容須與發送端 log 一致」的查核，修正 h6 語意 1/2

【目標】
只改 skill-lab/skill/.claude/skills/trace-notification/ 底下的檔案，分三點：
1. collect.py：receiver record 加 `payload_refund_requested`，取自收據 payload。sender record 加 `cancel_refund_requested`，取自同 notification_id 的 cancel log。再加 `payload_match`，值為 true、false 或 null，null 表示任一側缺欄位。
2. SKILL.md「查核迴圈」新增一步：收據與 log 的業務欄位（至少 refund_requested、kind）若不一致，視為收到的不是這則通知的正確內容。此時 receiver_status 填 unknown，missing_sources 寫「內容與發送端一致的接收端收據」，並在 next_action 說明是哪個欄位不一致。
3. 與前一案同步升版，併入 2.2.0；若兩案分開核准，則第二個核准的案子升 2.2.1。
與前一案一樣，不得動 check_result.py、gate.py 與受鎖檔案，也不得自己執行 eval.py。

【約束】
- 本卡由 loop engineer `l-03-skill-opt` 於 2026-10-04 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：只改 skill-lab/skill/；不得修改 cases/、expected.json、eval.py、eval/gate/（Stability_Goals 煞車）
- 不得破壞護欄：不得自己執行 skill-lab/eval.py（外層每天 01:50 在 main 上跑一次，成績寫進 skill-lab/scores/）；以成績單判斷，有退步不得送審（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. diff 只出現在 skill-lab/skill/ 之下；受鎖檔案雜湊與 main 一致
2. 以 h6 的 data 跑 collect.py，payload_match=false；以 complete、h1、h4 的 data 跑，payload_match=true
3. selftest.py 退出碼 0
4. 隔日外層 Eval 成績單中 h6 語意 =2/2，且其他案例的 semantic 不低於 day01
5. 成績單任何案例相對 day01 退步時不得送審

【證據】
觀測到的差距：h6-payload-mismatch 語意只對 1/2，不穩定。這個案例的收據 payload.refund_requested=false，與 log 中 cancel 事件的 refund_requested=true 相反。收到的內容不是這則通知的正確內容，正解是 receiver_status=unknown。SKILL.md 與 collect.py 都只用 order_id、notification_id、version 三個欄位比對收據，沒有要求比對 payload 內容，所以是否答對只取決於模型當次有沒有自己注意到。

SSOT：`order-service/skill-lab（scores/ 外層每日 Eval 成績單、skill/）`

- order-service/skill-lab/scores/day01.json：per_case.h6-payload-mismatch = {semantic:1, contract:2, runs:2}
- order-service/skill-lab/expected.json：h6-payload-mismatch → receiver_status=unknown，why=「收據的 refund_requested 與 log 相反：收到的不是這則通知的正確內容」
- order-service/skill-lab/cases/h6-payload-mismatch/data/logs.jsonl 第 2 行 cancel 事件 refund_requested=true；同案例 receipts.json 的 payload.refund_requested=false
- order-service/skill-lab/skill/.claude/skills/trace-notification/scripts/collect.py：receiver record 只帶 order_id/notification_id/version，沒有 payload 內容欄位
- order-service/skill-lab/skill/.claude/skills/trace-notification/SKILL.md「查核迴圈」：沒有任何比對收據內容與發送端事件內容的步驟
