# l-03-skill-opt|實驗3 優化 Skill：Eval 分數上升、零退步

【目標】
週期性依框架觀測 SSOT，比對「演化目標 vs 現況」的差距，每輪產出 1~N 張提案議題（state=review）進看板，由人逐案裁決後才執行。

【約束】
- 不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗（Stability_Goals 煞車）
- 產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo（Stability_Goals 煞車）
- 每輪預算 ≤ US$1，第一期合計 ≤ US$50（Stability_Goals 煞車）
- 只改 skill-lab/skill/；考題與正解不在 repo，不得從 git 歷史或其他位置取得（Stability_Goals 煞車）
- 不得自己執行 skill-lab/eval.py（外層每天 01:50 在 main 上跑一次，成績寫進 skill-lab/scores/）；以成績單判斷，有退步不得送審（Stability_Goals 煞車）
- 觀測與回寫的錨點只有 SSOT：`order-service/skill-lab（scores/ 外層每日 Eval 成績單、skill/）`（repo-native（git 可讀））
- 每輪只產提案（state=review），不產 code diff、不開分支；落地一律走人類裁決後的派工

【驗收】
1. 每輪產出的提案議題都附【證據】段（引用 SSOT 出處），可被逐案裁決
2. 本輪執行在該 routine 的 runs/ 留痕完整（成敗、產出、成本）

<!-- loopdeck:framework -->
## 迴路框架（三柱，由 LoopDeck 維護）

- **flavor**：loop engineer
- **執行時間（cron）**：`40 2 * * *`
- **SSOT（地基）**：`order-service/skill-lab（scores/ 外層每日 Eval 成績單、skill/）`（repo-native（git 可讀））

**Evolution_Goals（油門）**——這迴路要持續把 SSOT 推向的方向

- 語意正確數由基準 15/18 上升
- 吸收退回理由，同類理由退回次數下降

**Stability_Goals（煞車）**——演化過程不得破壞的護欄

- 不得修改 acceptance/（SPEC.md、run_acceptance.py）與 LOCK.json 鎖住的任何檔案；雜湊不符即判失敗
- 產出只能進 ld/<id> 分支，合併由人；不 push、不碰其他 repo
- 每輪預算 ≤ US$1，第一期合計 ≤ US$50
- 只改 skill-lab/skill/；考題與正解不在 repo，不得從 git 歷史或其他位置取得
- 不得自己執行 skill-lab/eval.py（外層每天 01:50 在 main 上跑一次，成績寫進 skill-lab/scores/）；以成績單判斷，有退步不得送審

<!-- /loopdeck:framework -->
