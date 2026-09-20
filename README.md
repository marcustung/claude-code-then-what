# 買了 Claude Code，然後呢？

**2026 iThome 鐵人賽・Claude AI 組・三十天系列的配套 repo。** 文章談的是一個工程團隊導入 Claude Code 之後，怎麼把「程式寫得更快」接回需求、審查、驗收與成效判斷；這裡放的是文章裡每一個實驗的原件——提示、trace、輸出、判準與重跑腳本——讓每一句「我試過」都能被打開來看。

- 系列文章：[iThome 系列頁](https://ithelp.ithome.com.tw/users/20162577/ironman/9862)（每日一篇，2026-09-15 起）
- 目前開放：Day 1–7（索引隨發文節奏開放，未發布的日子只有空資料夾）
- 試跑紀錄：[VERIFIED.md](VERIFIED.md)（每一天的練習都在乾淨副本裡照 README 跑過，含時間、環境、修過的問題）

## 這個 repo 是什麼、不是什麼

| 是 | 不是 |
|---|---|
| 每天一件 15 分鐘內能做完的練習，附可執行的指令與「跑完看什麼」 | 教學課程；文章本身在 iThome |
| 文章裡每次 Claude Code 實跑的完整原件：prompt、`stream-json` trace、輸出、meta、判準程式 | 公司程式、公司資料或任何成效數字 |
| 合成教學案例上的真實執行結果，含失敗與不如預期的 run | 統計結論；多數實驗各條件只跑一到三次 |
| 可以直接拿走的範本與審查套件 | 完整產品；未完成的東西不會出現在這裡 |

## 三分鐘開始

```powershell
git clone https://github.com/marcustung/claude-code-then-what.git
cd claude-code-then-what
# 不呼叫模型：讀一個歷史 run 的 trace，看它做了什麼
python tools/trace-summary.py days/day02/lab/day02-write
# 呼叫模型（需要已登入的 Claude Code CLI）：照任一天 README 的「跑什麼」執行，輸出會寫到新目錄，不覆寫歷史 run
```

需求依練習而異，各天 README 的「需要什麼」寫明：git、Claude Code CLI（`claude` 在 PATH 上，npm 或官方安裝器皆可）、.NET 9 SDK、Python 3、Node。呼叫模型的練習會消耗你自己的用量，每次約 US$0.01–0.15，各天 README 有實測費用。

## 目錄結構

```text
days/dayNN/          每天一個資料夾
  README.md          八格：文章｜今天練習｜需要什麼｜跑什麼｜看什麼｜範本｜原件｜界線｜最近試跑
  figures/           該篇文章的插圖
  lab/               該天的原件：runner、輸入、trace、輸出、判準（有實驗的日子才有）
shared/              真正跨天共用的 runner、protocol 與合成服務（出現時各天 README 會註明）
kit/                 可以拿走的最小實作，每一項都附一次可核對的執行紀錄
templates/           文章裡用到的表格範本，隨各天發布逐一出現
tools/               產圖與 trace 讀取工具
VERIFIED.md          讀者視角試跑紀錄
```

## 30 天索引

| Day | 題目 | 文章 | 關鍵詞 | 這裡能跑什麼 | 範本 |
|---|---|---|---|---|---|
| [1](days/day01/) | 買了 Claude Code，然後呢？ | [文章](https://ithelp.ithome.com.tw/articles/10411197) | 五層成效問題、AI 使用報表、git 署名統計、DORA、SPACE | 無實驗：歷史案例（使用報表），本篇留下問題與五層表 | [five-layers-ledger.md](templates/five-layers-ledger.md) |
| [2](days/day02/) | 這件事，真的需要 AI 嗎？ | [文章](https://ithelp.ithome.com.tw/articles/10412002) | 問題先於工具、人／程式／AI 分工卡、衡量口徑、Jira、Retro、ADR | days/day02/lab/day02-write：一句需求→程式＋測試＋假設 | [problem-first-card.md](templates/problem-first-card.md) |
| [3](days/day03/) | AI 寫程式很快，但為什麼我還是不敢 Approve | [文章](https://ithelp.ithome.com.tw/articles/10412647) | Headless 唯讀審查、假設清單、三層判級（工具→AI→Owner）、.NET 斷言測試、CODEOWNERS、CI、PR 交接契約 | days/day03/lab：一句需求→程式＋測試＋假設；kit/review：PR 範本、CODEOWNERS、判級規則、深挖清單、退件單、mermaid 圖 | [review-grade-handoff.md](templates/review-grade-handoff.md) |
| [4](days/day04/) | 退件之後，我改了什麼？ | [文章](https://ithelp.ithome.com.tw/articles/10412968) | Plugin、Skill、工具白名單、CLAUDE.md 不變條件、判級規則 R1–R5、審查 runner、GitHub Actions／Azure Repos 管線 | days/day04/lab、lab-dotnet、lab-plugin：退件後重跑、plugin 六次 run | [rejection-note.md](templates/rejection-note.md) |
| [5](days/day05/) | 先把尺放好，才知道工作有沒有變好 | [文章](https://ithelp.ithome.com.tw/articles/10413509) | JSON 輸出四欄（session、時間、回合、費用）、`/cost`、Session hook、設定隔離、JSONL 記錄器、基線卡、價值流、METR、SPACE／DevEx | days/day05/lab：G0-A 原始審查、V-G0-A 重跑、demo-01 練習；`claude -p --output-format json` 四欄 | [five-layers-ledger.md](templates/five-layers-ledger.md) |
| [6](days/day06/) | 別再猜我要什麼，先約好怎樣才算完成 | [文章](https://ithelp.ithome.com.tw/articles/10414144) | Spec 先於程式、intent／spec／plan、唯讀核對、分段放權、trace 讀檔核對、Mermaid 狀態圖、Given／When／Then 驗收 | days/day06/lab：intent／spec 核對、不指名實驗、驗收草稿、實作與觀察；lab-contract：契約檢查 | [problem-first-card.md](templates/problem-first-card.md) |
| [7](days/day07/) | 把老工程師腦中的「為什麼」交給 Claude | [文章](https://ithelp.ithome.com.tw/articles/10414658) | 理由卡、辨識標記、trace 交叉核對、負對照（無工具）、安全模式、CLAUDE.md 與 rules、`/context`、`/init`、exit code 不等於完成 | days/day07/lab：讀規則卡三次 | 無 |

## 怎麼核對一次 run

每個 `lab/` 裡的 run 目錄至少有四個檔：`prompt.txt`（送進去的提示）、`trace.jsonl`（Claude Code `--output-format stream-json` 的完整事件流：每次工具呼叫、工具回傳、最終回覆、回合數與費用估值）、`meta.json`（CLI 參數、起訖時間、exit code）、`stderr.txt`。

```powershell
python tools/trace-summary.py <run 目錄>                       # 回合、毫秒、費用、每次工具呼叫、回覆摘要
python tools/trace-summary.py <run 目錄> --marker <你埋的標記>   # 標記有沒有出現在工具回傳與回覆
```

文章裡的每個數字（回合、秒、費用、判斷結果）都取自這些檔案；有判準的實驗另附判準程式（如 `check_card.py`、`check_citations.py`），跑一次就能重算。

## 證據原則

1. **四種東西分開標**：合成教學案例、作者歷史工作的去識別敘述、模型實跑輸出、作者本機觀察。文章與各天 README 的「界線」欄寫明每一段屬於哪一種。
2. **只增不改**：歷史 run 目錄不覆寫；所有 runner 遇到既有輸出會寫到 `-rerun-<時間戳>` 新目錄或拒絕執行。
3. **失敗也留**：連線失敗、回覆不是 JSON、判斷答錯的 run 一樣保存並在文章裡說明。
4. **不做統計宣稱**：各條件多為一到三次；文章與 README 明寫「不是統計」。
5. **去識別**：路徑以 `<HOME>`、`<REPO>` 取代；不含公司名稱、人名、內部系統名。建置腳本在輸出前掃描，命中即拒絕產出。

## 怎麼用這裡的東西

- 直接複製 `templates/` 裡的表格到你的工單或 PR。
- `kit/` 裡的東西可以整個拿走；每一項的 README 有安裝與版本說明。
- 重跑實驗時改提示、改材料都可以，比較時記得只改一處，並把你的輸出留在新目錄。
- 發現跑不動或結果與 VERIFIED.md 差很多，開 issue 附你的環境與 run 名稱；這個 repo 由私有寫作 repo 的建置腳本產生，直接改這裡的檔案會在下次建置被覆寫，改動請走 issue。

## 授權

程式與範本以 [MIT](LICENSE) 授權。文章內容與插圖著作權屬作者；引用請註明 iThome 文章網址。
