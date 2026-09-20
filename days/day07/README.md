# Day 7｜把老工程師腦中的「為什麼」交給 Claude

| 格 | 內容 |
|---|---|
| 文章 | 未發 |
| 今天練習 | 挑一條你最常對 Claude 重複講的限制，寫成七欄理由卡，埋一個只有卡片裡有的標記，要求它回傳 |
| 需要什麼 | Claude Code CLI |
| 跑什麼 | `cd days/day07/lab; powershell -NoProfile -File run-day07-repeat.ps1; powershell -NoProfile -File run-day07-notools.ps1` |
| 看什麼 | python tools/trace-summary.py days/day07/lab/day07-r2-rerun-* --marker RULE-CONTEXT-7-KITE-0911：Read 一次、標記在工具回傳與回覆各出現；再對 notools-rerun-* 跑一次：0 次工具呼叫、標記 False、exit 仍是 0 |
| 範本 | 無 |
| 原件 | days/day07/lab（day07、day07-r2、day07-r3、負對照 day07-notools-1／2、rule-card.md）；lab-compact（原版／精簡版各三次） |
| 界線 | 顯式 Read，不是 CLAUDE.md 自動載入；三次不是統計 |
| 最近試跑 | 2026-09-20 14:21（E1）OK：r2／r3 重跑：1 次 Read、標記在工具回傳與回覆、五項 [false,false,false,true,true]；notools 重跑：0 次工具呼叫、無標記、exit 0。修正：所有 runner 原本硬寫作者機器上的 claude.exe 路徑（公開版被去識別成 <HOME>，讀者跑不動），改為從 PATH 找 claude.exe／claude.cmd，找不到印安裝提示；見 [VERIFIED.md](../../VERIFIED.md) |

[回 30 天索引](../../README.md)
