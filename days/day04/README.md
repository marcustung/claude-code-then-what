# Day 4｜退件之後，我改了什麼？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10412968) |
| 今天練習 | 用 --plugin-dir 載入 review-kit，審 fixtures/pr-A，對照 runs/ 裡的結果 |
| 需要什麼 | Claude Code CLI |
| 跑什麼 | `cd kit/review/plugin-lab; powershell -NoProfile -File run-verify.ps1   # 三次呼叫約 90 秒，跑完自動 extract＋R1–R5 check` |
| 看什麼 | 三次 check 的 R1–R5；載入 plugin 那次（V-S-A）R5 應為 true、findings 較少但每則有來源。歷史結果在 days/day04/lab-plugin/verify-20260918 與 days/day05/lab/V-G0-A |
| 範本 | [rejection-note.md](../../templates/rejection-note.md) |
| 原件 | days/day04/lab（review-poc）、lab-dotnet、lab-plugin（G0-B、S-A、S-B、round1、verify-20260918 的 V-G0-B／V-S-A）；plugin 本體在 kit/review/plugin-lab |
| 界線 | 合成 PR；歷史退件（08-07、08-12）只在文章正文 |
| 最近試跑 | 2026-09-20 14:15（E1）OK：三段都通過；plugin 三次呼叫 93 s，V-G0-A／V-G0-B／V-S-A 的 R1–R5 全 true（V-S-A R5=true）。修正：run-verify.ps1 原本讀已搬走的 runs/G0-A、runs/S-A 提示（讀者跑會找不到檔），改讀 prompts/；輸出改為時間戳目錄；跑完自動 extract＋check；extract_result.py／check_card.py 改為接受任意路徑；見 [VERIFIED.md](../../VERIFIED.md) |

[回 30 天索引](../../README.md)
