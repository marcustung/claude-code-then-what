# Day 15｜Claude 協助驗的功能，大家一起用還正常嗎？

| 格 | 內容 |
|---|---|
| 文章 | 未發 |
| 今天練習 | 拿 Day 14 的同一份發布包跑負載，再把假接收端改成延遲 300ms 跑第二次：API 門檻兩次都過，通知接收紀錄卻不一樣 |
| 需要什麼 | Python 3；.NET 9 SDK；k6；Docker（Prometheus／Grafana 可選） |
| 跑什麼 | `cd days/day14/lab-delivery; python day15-lab/run-load.py my-sustain --profile sustain --k6 k6` |
| 看什麼 | runs/my-sustain 的 k6 摘要：首次取消 p95 應低於 250ms、http_req_failed 為 0、dropped_iterations 為 0。再比對已保存的兩組對照 runs/day15-skill-control-01 與 day15-skill-slow-01：receipts.json 筆數一個是 201、一個只有 127，而兩組的 k6 API 門檻都通過——差別在 report.json 的 passed（true／false） |
| 範本 | 無 |
| 原件 | days/day14/lab-delivery：day15-lab（計畫、腳本、儀表板設定、Claude 回覆）、day15-skill-lab（官方 planner Skill 的載入紀錄）、runs/day15-smoke-01／spike-01／sustain-01（三輪負載）、runs/day15-skill-control-01／skill-slow-01（正常與慢下游對照） |
| 界線 | 本機單機 loopback、記憶體儲存、假接收端；短時教學驗證，不是容量上限或長時間穩定性；201／127 是觀察截止的紀錄，不代表 74 筆永久遺失；無 Production 部署與公司 SLA |


[回 30 天索引](../../README.md)
