# Day 4｜退件之後，我改了什麼？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10412968) |
| 今天練習 | 用 --plugin-dir 載入 review-kit，審 fixtures/pr-A，對照 runs/ 裡的結果 |
| 需要什麼 | Claude Code CLI |
| 跑什麼 | `cd kit/review/plugin-lab; powershell -NoProfile -File run-verify.ps1   # 結果對照 days/day04/lab-plugin/verify-20260918` |
| 看什麼 | 它有沒有把「已取消再取消」列為待確認；R1–R5 五格對不對 |
| 範本 | [rejection-note.md](../../templates/rejection-note.md) |
| 原件 | days/day04/lab（review-poc）、lab-dotnet、lab-plugin（G0-B、S-A、S-B、round1、verify-20260918 的 V-G0-B／V-S-A）；plugin 本體在 kit/review/plugin-lab |
| 界線 | 合成 PR；歷史退件（08-07、08-12）只在文章正文 |

[回 30 天索引](../../README.md)
