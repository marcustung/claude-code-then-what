# Day 5｜先把尺放好，才知道工作有沒有變好

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10413509) |
| 今天練習 | 跑一次 claude -p --output-format json，把四個欄位抄進工作卡；人工五格填未知或估 |
| 需要什麼 | Claude Code CLI |
| 跑什麼 | `claude -p "讀取 PR.md、ticket.md、diff.patch、Program.cs，僅審查，不修改檔案。用三句話說明這份 PR 缺什麼依據。" --model sonnet --effort low --safe-mode --tools Read,Grep,Glob --allowedTools Read,Grep,Glob --output-format json > run-demo.json` |
| 看什麼 | session_id、duration_ms、num_turns、total_cost_usd；你自己那五格有幾格是空的。沒有自己的 PR 就先用 kit/review/plugin-lab/fixtures/pr-A 那四個檔 |
| 範本 | [five-layers-ledger.md](../../templates/five-layers-ledger.md) |
| 原件 | days/day05/lab（G0-A 原始審查、V-G0-A 重跑、demo-01 練習；含 trace、result、meta） |
| 界線 | G0-A 原始審查原件另附；合成分鐘數不是工時；不含省時結論 |
| 最近試跑 | 2026-09-20 14:18（E1）OK：11 s、5 回合、US$0.03、is_error=false、subtype=success，四個欄位都在。修正：fixtures/pr-A 裡多一個 09-17 留下的 run-demo.json，已移出；見 [VERIFIED.md](../../VERIFIED.md) |

[回 30 天索引](../../README.md)
