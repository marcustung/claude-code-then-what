# Day 26｜CPU 正常，服務卻卡住了，Claude 能查出為什麼嗎？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10422890) |
| 今天練習 | CPU 正常、服務卻卡住：讓 Claude 只用唯讀 MCP 查 Grafana 指標、Log、堆疊與程式找出同步等待（ThreadPool 飢餓）；另開工作階段修，第一版速度恢復卻被同單 16 併發攔下，第二版鎖內讀取、判斷、更新才過關；另附第三方題庫成績 |
| 需要什麼 | Python 3、.NET 9 SDK（重跑最終修法驗收，不需 Claude 或 Grafana）；重跑 Claude 查因需 Day 24 的本機 Grafana、gcx 與 Claude Code CLI |
| 跑什麼 | `python days/day26/lab-threadpool/validate_claude_repair.py --workspace days/day26/lab-threadpool/claude-final-source` |
| 看什麼 | lab-threadpool 的 CLAUDE-VERIFICATION.md；claude-a 三次查因的 card.json 與 tool-audit.jsonl；claude-b 兩版的 answer.md 與 diff.patch；repair-validation 的 summary.json 與 same-order.json；lab-bench/README.md 的題庫成績 |
| 範本 | [diagnosis-card.md](../../templates/diagnosis-card.md) |
| 原件 | days/day26/lab-threadpool（criteria.md、claude-criteria.md、REPORT.md、CLAUDE-VERIFICATION.md、prepare.py、run.py、claude_investigate.py／claude_repair.py／claude_repair_followup.py、validate_claude_repair.py、claude-final-source）；days/day26/lab-bench（RCAEval 40 次與 o11y-bench 三組各 40 次成績）；舊六次快照診斷在 days/day26/lab/diagnosis-oom |
| 界線 | 本機故障注入、非歷史公司事故或容量測試；DOTNET_PROCESSOR_COUNT=2 只是 runtime 提示；查因用重放資料、堆疊另輪取得；未完全排除 GC 與所有鎖競爭；題庫成績只代表該題型，不是診斷正確率 |


[回 30 天索引](../../README.md)
