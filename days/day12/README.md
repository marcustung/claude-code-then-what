# Day 12｜Claude 寫的程式通過單元測試，API 也接對了嗎？

| 格 | 內容 |
|---|---|
| 文章 | 未發 |
| 今天練習 | 跑一次驗證者→實作者→新驗證的完整週期：外層先在隔離副本故意接錯一個通知欄位，讓 Claude 用 verifier 角色跑測試找出來，換一個修正呼叫只改該處，再用新上下文重新驗證同一套檢查 |
| 需要什麼 | Python 3；.NET 9 SDK；重跑 Claude 分析需 Claude Code CLI 並已登入 |
| 跑什麼 | `cd days/day11/lab-dev; python verify-integration.py reader-integration-02; python run-verifier-cycle.py reader-verifier-01` |
| 看什麼 | 第一個指令的 {checks:11, pass:true}。第二個指令跑完看 runs/reader-verifier-01/report.json：status 應為 VERIFIED，failed_checks_before 應為 [notification-ids-and-flags]，green_checks 應為 11。repair.diff 應只改 src/Api/Program.cs 一行（false → result.RefundRequested） |
| 範本 | 無 |
| 原件 | days/day11/lab-dev（與 Day 11 共用同一份開發包）：runs/verifier-cycle-01（本次 verifier 實跑）、verify-integration.py、run-verifier-cycle.py；runs/boundary-01、integration-01、boundary-negative-01／02 為歷史原件保留，不是本輪成果 |
| 界線 | 外層注入的是既定錯誤，不是模型自然犯的；新上下文仍共用同一份規格與驗證器，不是獨立真值來源；本機 loopback，無正式部署 |
| 最近試跑 | 2026-09-26 06:27（E1）OK：verify-integration：{checks:11, pass:true}。run-verifier-cycle：三段 exit 0，status=VERIFIED；report.json 的 failed_checks_before=[notification-ids-and-flags]、green_checks=11、protected_unchanged=true 與正文一致；repair.diff 只改 Program.cs 一行（false → result.RefundRequested），與正文 C# 前後對照逐字相符。三段 trace.jsonl 均有真實 tool_use（13／5／12 次），非純文字摘要。本次三段合計 123 秒／US$0.446；正文寫的是作者原始那次的 219 秒／US$0.527（見 runs/verifier-cycle-01）。時間差了近一倍，不只是計價浮動——重驗每次回合數與模型思考長度都會變，正文用「約」字已預留這個範圍，讀者重跑本就不會拿到同一個數字，只有『流程走完、發現一致』才是這篇要驗的事。；見 [VERIFIED.md](../../VERIFIED.md) |

[回 30 天索引](../../README.md)
