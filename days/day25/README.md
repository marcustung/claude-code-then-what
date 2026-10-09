# Day 25｜看著 Dashboard，要怎麼知道訂單卡在哪？

| 格 | 內容 |
|---|---|
| 文章 | 未發 |
| 今天練習 | 看三層各自怎麼被抓到「看起來對、其實不對」：Claude 寫的核對程式跑八項檢查、Dashboard 第一版到第七版的驗收原話、調查卡四輪的事前判準與查詢摘要 |
| 需要什麼 | Python 3（重算檢查）；重跑 Grafana 送資料需 Day 24 的本機 Grafana 與原始紀錄（之後的日次公開） |
| 跑什麼 | `cd days/day25/lab-dashboard; 先讀 README；python check_ai_card_plain.py runs-ai-card/20261009T005823Z-plain2/ai-cards.json` |
| 看什麼 | runs-claude 兩輪的 grading.json（八項過幾項）；runs-claude-dashboard 各版的 answer.md 與 screenshot.png；ai-card-plain-criteria.md 第三輪把查不到寫成沒有、第四輪改正 |
| 範本 | 無 |
| 原件 | days/day25/lab-dashboard（build.py 與核對結果 runs/、Claude 寫核對程式兩輪、Dashboard 15 次執行、調查卡四輪、各版事前判準與偏離紀錄） |
| 界線 | 教學紀錄重放、本機 Grafana；每次 sonnet 各跑一次；驗收人只有作者；原始紀錄未隨本篇公開 |


[回 30 天索引](../../README.md)
