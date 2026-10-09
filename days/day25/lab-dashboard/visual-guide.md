# Day 25 圖片與原始截圖

正文局部放大只是閱讀排版，未改動實跑數據，也未重新產生實跑畫面。

- [完整前後對照](../../assets/diagrams/v12/investigation-notes/day25-dashboard-before-after-r3.png)
- [原始 AI 調查卡](../../assets/diagrams/v12/investigation-notes/day25-ai-card-r1.png)
- [三個問題局部對照](../../assets/diagrams/v12/investigation-notes/day25-dashboard-before-after-r5.png)
- [AI 調查卡放大](../../assets/diagrams/v12/investigation-notes/day25-ai-card-r3.png)
- [規則與 AI 分工示意](../../assets/diagrams/v12/investigation-notes/day25-rules-ai-routing-r2.png)

重製入口：tools/gen-day25-screenshot-notes.py，再以 tools/export-diagram-png.py 匯出；截圖 HTML 選取 .sheet；分工概念圖以 imagegen 生成，提示另存圖片旁的 .prompt.md。需安裝現有 Python Playwright 環境。

分工圖為概念示意。真正的查詢、資料界線與接受條件，仍以正文和實跑紀錄為準。退款優先是模型建議，未當作已批准的規則。
