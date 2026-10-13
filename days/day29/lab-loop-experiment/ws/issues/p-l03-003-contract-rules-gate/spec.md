# p-l03-003-contract-rules-gate|SKILL.md 補齊固定檢查器的錯誤碼規則與退出碼 2 的處理，針對 c04、c07 契約連續 0/2

【目標】
只改 skill-lab/skill/.claude/skills/trace-notification/ 底下的檔案，不動 check_result.py、gate.py 與受鎖檔案。(1) SKILL.md「輸出」第 3 點新增「寫 result.json 前自檢」清單，逐條對應 check_result.py 現有規則，不寫任何案例專屬內容：欄位齊全；schema_version=1；三個 ID 須等於 collect.py 產出的值；兩個 status 只能是 confirmed 或 unknown；某側標 confirmed 時，evidence_refs 必須包含該側對應事件（sender 為 notify_sent，receiver 為 notification_received）且三個 ID 吻合的 ref；receiver_status=unknown 時 missing_sources 至少一項具體說明缺什麼；confirmed 時 missing_sources 必須為空陣列。(2) 同處補上退出碼 2：讀 gate 輸出的 errors，若是 NOTIFICATION_ID_NOT_UNIQUE 或 RESULT_FILE_MISSING，不得竄改 data/ 或腳本去繞過，應在 next_action 如實寫明卡點並保留 result.json。(3) CHANGELOG 與 VERSION 升到 2.1.3，並在 SKILL.md 版本段記一行。只可執行 selftest.py，不得執行 eval.py。

【約束】
- 本卡由 loop engineer `l-03-skill-opt` 於 2026-10-07 這一輪觀測產出，尚未經人類裁決
- 不得破壞護欄：不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 不得破壞護欄：產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 不得破壞護欄：每輪預算 ≤ US$2，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 不得破壞護欄：只改 skill-lab/skill/；考題與正解不在 repo，不得從 git 歷史或其他位置取得（Stability_Goals 煞車）
- 不得破壞護欄：不得自己執行 skill-lab/eval.py（外層每天 01:50 在 main 上跑一次，成績寫進 skill-lab/scores/）；以成績單判斷，有退步不得送審（Stability_Goals 煞車）
- 產出走既有派工流程（worktree → diff → 人類合併），不得繞過裁決直接落地

【驗收】
1. diff 只出現在 skill-lab/skill/ 之下，且只涉及 SKILL.md、CHANGELOG.md、VERSION；acceptance/、LOCK.json 鎖定檔案與 check_result.py、gate.py 的雜湊與 main 一致
2. SKILL.md 內新增的自檢清單涵蓋 check_result.py 全部錯誤碼類別，並明寫退出碼 2 的處置；內容不含任何案例名稱、考題或正解
3. selftest.py 退出碼 0
4. 隔日外層 Eval 成績單：contract_ok 不低於 14/18；各案例 semantic 不低於 day01 與 day04 取較高者（以 day04 為準的逐案比較，c08 的日間波動另計）
5. 若 c04、c07 的 contract 仍為 0/2，須在回報中說明這很可能是結構性問題（例如 INPUT_ERROR 無法由 Skill 側解除），不再重複以相同做法提案

【證據】
觀測到的差距：契約（contract）通過數卡在 14/18。c04、c07 自 day01 到 day04 每天都是 semantic 2/2、contract 0/2：模型判斷對了，但 out/result.json 沒過固定檢查。4 天 skill 版本都是 2.1.2，沒有任何自行改善的跡象。SKILL.md「輸出」第 3 點只寫了 gate.py 退出碼 0 和 1，沒有寫退出碼 2（INPUT_ERROR）該怎麼辦。check_result.py 才有的硬規則也沒寫進 SKILL.md：receiver_status=unknown 時 missing_sources 不得為空；confirmed 時 missing_sources 必須為空；confirmed 必須引用同側、同事件、三個 ID 都吻合的 evidence_refs。模型只能靠讀檢查器原始碼或撞錯誤碼才知道，而 SKILL.md 又只允許補查一次。這是依成績單失分模式與 skill 本體推得的假設。考題不在 repo，無法直接確認 c04、c07 的失敗原因。

SSOT：`order-service/skill-lab（scores/ 外層每日 Eval 成績單、skill/）`

- order-service/skill-lab/scores/day01.json～day04.json：per_case.c04 與 c07 四天皆為 {semantic:2, contract:0, runs:2}；各日 contract_ok=14/18、skill_version=2.1.2
- order-service/skill-lab/skill/.claude/skills/trace-notification/SKILL.md「輸出」第 3 點：只列「退出碼 0」與「退出碼 1」，沒有退出碼 2，也沒有列出錯誤碼規則；且「最多一次」補查
- order-service/skill-lab/skill/.claude/skills/trace-notification/scripts/check_result.py：UNKNOWN_NEEDS_MISSING_SOURCE、CONFIRMED_WITH_MISSING_SOURCE、SENDER_EVIDENCE_REQUIRED、RECEIVER_EVIDENCE_REQUIRED、UNKNOWN_SOURCE_REF 等規則未見於 SKILL.md
- order-service/skill-lab/skill/.claude/skills/trace-notification/scripts/gate.py：len(notification_ids)!=1 或 result 檔不存在時回 INPUT_ERROR、退出碼 2，SKILL.md 沒有說明這種情況的處置
- order-service/skill-lab/skill/.claude/skills/trace-notification/CHANGELOG.md：2.0.2 曾因 sender_status 規則沒寫進 SKILL.md 而被退回，同類缺口曾出現過
