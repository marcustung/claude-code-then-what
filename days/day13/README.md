# Day 13｜Claude 審過、測試也過，為什麼還要找 Owner？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10417738) |
| 今天練習 | 對 Day 11 的 Domain diff 跑一次不呼叫模型的路徑政策，再對照 review-kit 兩輪審查的原件：哪一項退件是誤判、哪一項補件後仍是 OWNER_REQUIRED |
| 需要什麼 | Python 3；重跑 plugin 審查需 Claude Code CLI 並已登入 |
| 跑什麼 | `cd days/day11/lab-dev; python route-review.py --selftest; python route-review.py` |
| 看什麼 | 第二個指令的 route 應為 OWNER_REQUIRED、owner_hits 含 src/Domain/Cancellation.cs、reason 為 core path。再開 runs/plugin-review-01/result.md 找「tests.txt does not exist」，對照 runs/impl/tests.txt 確實存在、七個情境 PASS |
| 範本 | 無 |
| 原件 | days/day11/lab-dev（與 Day 11–12 共用開發包）：route-review.py、routing-policy.json、runs/plugin-review-01／02（提示、trace、回覆）、runs/impl/tests.txt |
| 界線 | 沒有真人 Owner 簽核、沒有遠端 PR；路徑政策只示範保守升級，不代表能辨識所有核心業務 |


[回 30 天索引](../../README.md)
