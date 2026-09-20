# Day 2｜這件事，真的需要 AI 嗎？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10412002) |
| 今天練習 | 拿一件你正想交給 Claude 的工作，填「要解決什麼／期待什麼／如何衡量／誰追」四格 |
| 需要什麼 | 無 |
| 跑什麼 | `cd days/day02/lab; powershell -NoProfile -File run-day02.ps1; python check-day02.py day02-write-rerun-<時間戳>` |
| 看什麼 | 四格填不出來的那一格，就是先別交給工具的原因。想看 Claude 拿到一句需求會補什麼假設：跑 runner（會呼叫 Claude），再用 check-day02.py 抽出程式、跑六個情境 |
| 範本 | [problem-first-card.md](../../templates/problem-first-card.md) |
| 原件 | days/day02/lab/day02-write（歷史 run：prompt、trace、answer.json、Guard.cs、check/ 六情境） |
| 界線 | 合成需求、單次執行 |
| 最近試跑 | 2026-09-20 14:13（E1）OK：Claude 13 s 交回 JSON；抽出 Guard.cs 後六個情境 6 passed, 0 failed。修正：原本沒有抽出／編譯步驟，新增 check-day02.py；見 [VERIFIED.md](../../VERIFIED.md) |

[回 30 天索引](../../README.md)
