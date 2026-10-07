# Day 24｜通知慢在哪？先讓系統說話，Claude 才查得清楚

| 格 | 內容 |
|---|---|
| 文章 | 未發 |
| 今天練習 | 從規格決定要留的訊號，用 OpenTelemetry 補排隊時間與跨背景工作的 Trace，再透過唯讀 MCP 呼叫 gcx 讓 Claude 自己查；比較補觀測前後能回答什麼 |
| 需要什麼 | Windows、Docker Desktop、.NET 9 SDK、Python 3、gcx；最後一步需 Claude Code CLI |
| 跑什麼 | `cd days/day24/lab-observability; python setup.py; python run.py; python verify.py; python run-claude.py` |
| 看什麼 | 四輪都 9／9 且零重複；verify.py 四項 PASS；after-slow-8 的排隊約 2,187 ms 對 API 約 1.6 ms；Claude 對修改前寫未知、查詢錯誤不當結果 |
| 範本 | 無 |
| 原件 | days/day24/lab-observability（before／after 程式、四輪原始紀錄、後端回傳、Claude 提示與工具紀錄）；days/day24/order-cancel-lifecycle（核對原始版本用的 6 個檔與通知契約） |
| 界線 | 本機教學服務、每種條件一輪每輪九筆、慢下游刻意設定 250 ms；Claude 只完整拆解一筆；不宣稱省時或診斷準確率 |


[回 30 天索引](../../README.md)
