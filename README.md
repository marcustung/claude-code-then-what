# 買了 Claude Code，然後呢？——系列配套 repo

2026 iThome 鐵人賽 Claude AI 組系列（[系列頁](https://ithelp.ithome.com.tw/users/20162577/ironman/9862)）的可重跑部分。三十天，每天一件 15 分鐘的事，每件事留下能核對的原件。文章在 iThome（連結見各日），這裡放三種東西：

- `days/dayNN/`：每天一個資料夾。`README.md` 八格（文章、今天練習、需要什麼、跑什麼、看什麼、範本、原件、界線）；那天自己的原件在 `lab/`（runner、輸入、trace、輸出），插圖在 `figures/`。歷史案例的日子只有 README 與範本連結，README 會寫明。
- `shared/`：真正跨天共用的東西（runner、protocol、共用的合成服務），出現時各天 README 會說用了哪一部分。
- `templates/`：文章裡用到的表格範本，直接複製去用；隨各天發布逐一出現。
- `tools/`：產圖腳本（各篇插圖在 `days/dayNN/figures/`，可重出）。
- `kit/`：能拿走的最小實作；各項完成並有一次執行紀錄後才出現，未完成的不放半成品。

**不在這裡的**：公司歷史案例的原件（去識別後只在文章正文引用）、規劃與審稿文件、封面、作者自己的工作脈絡。文章裡標「歷史」的日子在這裡只有範本。

## 30 天索引

索引隨發文節奏開放：只列已發布的日子，明天的內容明天再出現。

| Day | 題目 | 文章 | 這裡能跑什麼 | 範本 |
|---|---|---|---|---|
| [1](days/day01/) | 買了 Claude Code，然後呢？ | [文章](https://ithelp.ithome.com.tw/articles/10411197) | —（歷史案例：使用報表；本篇只有問題與五層表） | [five-layers-ledger.md](templates/five-layers-ledger.md) |
| [2](days/day02/) | 這件事，真的需要 AI 嗎？ | [文章](https://ithelp.ithome.com.tw/articles/10412002) | days/day02/lab/day02-write：一句需求→程式＋測試＋假設 | [problem-first-card.md](templates/problem-first-card.md) |
| [3](days/day03/) | AI 寫程式很快，但為什麼我還是不敢 Approve | [文章](https://ithelp.ithome.com.tw/articles/10412647) | days/day03/lab：一句需求→程式＋測試＋假設；kit/review：PR 範本、CODEOWNERS、判級規則、深挖清單、退件單、mermaid 圖 | [review-grade-handoff.md](templates/review-grade-handoff.md) |
| [4](days/day04/) | 退件之後，我改了什麼？ | [文章](https://ithelp.ithome.com.tw/articles/10412968) | days/day04/lab、lab-dotnet、lab-plugin：退件後重跑、plugin 六次 run | [rejection-note.md](templates/rejection-note.md) |
| [5](days/day05/) | 先把尺放好，才知道工作有沒有變好 | [文章](https://ithelp.ithome.com.tw/articles/10413509) | days/day05/lab：G0-A 原始審查、V-G0-A 重跑、demo-01 練習；`claude -p --output-format json` 四欄 | [five-layers-ledger.md](templates/five-layers-ledger.md) |
| [6](days/day06/) | 別再猜我要什麼，先約好怎樣才算完成 | [文章](https://ithelp.ithome.com.tw/articles/10414144) | days/day06/lab：intent／spec 核對、不指名實驗、驗收草稿、實作與觀察；lab-contract：契約檢查 | [problem-first-card.md](templates/problem-first-card.md) |

## 重跑最小路徑

不呼叫模型的離線核對，看各天 README 的「跑什麼」；需要 Claude Code CLI 的 lab 都附 trace，可以不重跑只對照。

## 資料說明

所有 run 皆為合成任務的真實執行輸出；不含任何企業成效數字。路徑已以 `<HOME>`、`<REPO>` 取代。模型與 CLI 版本以各 lab 的 meta／manifest 為準。
