# Day 27｜通知逾時了，能不能請 Claude 直接重送？

| 格 | 內容 |
|---|---|
| 文章 | 未發 |
| 今天練習 | 通知逾時後，先查接收端「做了沒」再決定：已完成不重送、確認未完成才重送、查不到就停；Claude 只交提案，重送走固定入口（再查一次、核對凍結、授權與次數）；凍結題重跑 30 次，看 Claude 按不按取決於什麼 |
| 需要什麼 | Python 3、.NET 9 SDK（重跑固定流程）；重跑 Claude 需 Claude Code CLI |
| 跑什麼 | `cd days/day27/lab-recovery; python verify.py` |
| 看什麼 | lab-recovery 的 runs/<最新>/summary.json（三情境副作用與九項檢查）、runs-claude 的三份 proposal.json；lab-pressure 的 runs-claude/summary.json（S1 凍結被擋、S2 重送一次），以及 runs-claude/20261010T135337Z 與 20261010T140351Z 的 repeat-summary.json（凍結題重跑 30 次） |
| 範本 | [grading-table.md](../../templates/grading-table.md) |
| 原件 | days/day27/lab-recovery（protocol.json、src/、controller.py、verify.py、claude-criteria.md、run-claude.py、runs、runs-claude）；days/day27/lab-pressure（claude-criteria.md、run-claude.py、repeat-criteria.md、repeat-frozen.py、repeat-frozen-rule.py、figures/、runs-claude）；days/day27/lab 是 Day 16 共同範例的故障檔與故障 run，依當時約定於本篇公開 |
| 界線 | 記憶體去重、單程序、本機 HTTP；不保證跨重啟或分散式安全；demo-owner 是測試設定；Claude 查證三題與未凍結題各一次，凍結題重跑 30 次（每種訊息 5 次，只看方向） |


[回 30 天索引](../../README.md)
