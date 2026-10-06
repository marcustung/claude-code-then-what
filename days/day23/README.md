# Day 23｜上線後都沒報錯，監控真的看得到問題嗎？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10421896) |
| 今天練習 | 拿修正前後兩版程式與四次執行紀錄，先用固定對帳程式重算 9／3 的落差，再請 Claude 沿同一筆通知對照契約、Log 與程式，找出延後分支為何被記成已送出 |
| 需要什麼 | Python 3（重算）；Claude Code CLI（對照分析） |
| 跑什麼 | `cd days/day23/lab-notify; 依 README 複製 runs/ 後執行 python tools/check.py <副本>` |
| 看什麼 | 故障版 FAIL：接收端 3、sent_total 9；修正版 PASS 並有 45 次延後重排；claude-run/ 三次是否都指到延後分支的 continue |
| 範本 | 無 |
| 原件 | days/day23/lab-notify（v1.0.0／v1.1.0 程式、四次 runs、check.py、通知契約、claude-run 的提示與 3 次輸出） |
| 界線 | 本機教學服務、刻意注入的單一故障；每版各跑一次，Claude 同資料 3 次，不估準確率；未驗持續超載與補送 |


[回 30 天索引](../../README.md)
