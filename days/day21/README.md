# Day 21｜Skill 改了，怎麼知道沒改壞？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10421083) |
| 今天練習 | 改 Skill 前先寫死正解，拿「不帶 Skill／舊版／新版」三種條件各跑 3 次，用不採信自述的 gate.py 量語意與契約 |
| 需要什麼 | Claude Code CLI、Python 3 |
| 跑什麼 | `cd days/day21/lab-eval; python run-eval.py 3` |
| 看什麼 | 語意欄與契約欄分開看：契約 0/9 不是答錯；回歸案例 6/6、誘餌 0 誤判、v2 契約 9/9 是之後每一版的門檻 |
| 範本 | 無 |
| 原件 | days/day21/lab-eval（run-eval.py 的 EXPECTED、27 次軌跡、runs/20261003-044716/SUMMARY.md、FINDINGS.md）；難考卷在 lab-eval/hard（expected.json、兩組各 18 次的 summary 與軌跡；run_noskill.py 依賴作者本機 skill-lab，僅供對照） |
| 界線 | 同一模型、每組 3 次、教學資料，不估準確率；契約格式由 v2 定義，對其他條件不公平 |


[回 30 天索引](../../README.md)
