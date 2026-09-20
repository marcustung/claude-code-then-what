# Day 6｜別再猜我要什麼，先約好怎樣才算完成

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10414144) |
| 今天練習 | 把一句需求寫成 intent.md 與 spec.md，先讓 Claude 唯讀核對方向，再整理驗收草稿；不要先寫程式 |
| 需要什麼 | Claude Code CLI；.NET 9（重跑 impl） |
| 跑什麼 | `cd days/day06/lab; powershell -NoProfile -File run-intent.ps1; powershell -NoProfile -File run-noname.ps1` |
| 看什麼 | 跑完 python tools/trace-summary.py days/day06/lab/noname-rerun-*：工具呼叫那行有沒有 Read intent.md（歷史 run 沒有；每次回覆會不同，這一點不會變） |
| 範本 | [problem-first-card.md](../../templates/problem-first-card.md) |
| 原件 | days/day06/lab（diagram、intent、noname、draft、impl、impl-check 六個目錄）；lab-two-stage（另一次兩階段唯讀驗證）；lab-contract |
| 界線 | DEMO-DECISION-01 是教學假設；合成訂單 |
| 最近試跑 | 2026-09-20 14:20（E1）OK：各寫到 *-rerun-時間戳 新目錄，歷史 run 未動。intent 3 回合讀兩檔；noname 3 回合未讀 intent.md（這次它沒猜 spec.md，改要求提供路徑；結論不變）。修正：新增 tools/trace-summary.py 讓讀者一行看到工具呼叫；見 [VERIFIED.md](../../VERIFIED.md) |

[回 30 天索引](../../README.md)
