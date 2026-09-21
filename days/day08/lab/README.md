# Day 8 引用抽驗實驗（2026-09-19）

目的：Day 8 的歷史案例（答案卷更正）原件私有。這裡用一個教學示範 repo 重建同一個結構，讓「每個結論附檔案:行號，再抽驗」這條規則變成讀者能重跑的東西。

## 內容

- `repo/`：7 個 C# 檔、167 行，只供讀取，未編譯。報表入口 `Reports/DependentReportController.cs` → `DependentRepository.ListForPayrollGroup`（WHERE 只有公司／員工／群組，生效日只在 SELECT）→ `DependentCountService.Count`（LINQ 直接數）。另一支 `ListEffectiveInPeriod` 有日期條件，被 `MonthlyTaxCalculator`（計薪端，含 `AddDays` 加 `<=` 的端點問題）、`BonusCalculator`、`SeveranceSettlement`、`PayslipPrinter` 呼叫。名稱、欄位、SQL 全為示例。
- `answer-key-v1.md`：故意保留當年錯答的答案卷（報表走有日期條件的查詢、兩症狀共用過濾）。**Claude 沒有讀到這份**。
- `prompt.txt`：五個問題；規則是每個結論附「檔案路徑:行號」，行號必須是實際讀到的那一行，讀不到寫「未讀到」；只回 JSON。
- `run.ps1`：`claude -p --model sonnet --effort low --tools Read,Grep,Glob --allowedTools Read,Grep,Glob --strict-mcp-config --no-session-persistence --setting-sources "" --output-format stream-json --verbose`，工作目錄 `repo/`，stdin 以 UTF-8 送入。
- `check_citations.py`：從 trace 取最終 JSON，對每筆引用印該行前後一行；核對檔案存在、行號在範圍內、**該行號是否出現在 trace 內 Read／Grep 的工具回傳**（Read 回傳每行自帶行號）。
- `runs/r1..r3/`：trace.jsonl、stderr.txt、meta.json。

## 結果

| run | 回合 | 秒 | 費用估值 | 引用筆數 | 檔案存在・行號在範圍・trace 讀到過 | 報表走哪支 | 有日期條件 | 計數看日期 | 共用過濾 | 修計薪端報表會好 |
|---|---|---|---|---|---|---|---|---|---|---|
| r1 | 8 | 28.6 | US$0.081 | 13 | 13／13 | ListForPayrollGroup | 否 | 否 | 否 | 否 |
| r2 | 7 | 26.6 | US$0.049 | 11 | 11／11 | ListForPayrollGroup | 否 | 否 | 否 | 否 |
| r3 | 7 | 25.3 | US$0.046 | 13 | 13／13 | ListForPayrollGroup | 否 | 否 | 否 | 否 |

三次都用 Glob → Read ×4 → Grep 追鏈，都列出四個 `ListEffectiveInPeriod` 呼叫端。r2、r3 的 unknowns 寫明三個 Payroll 呼叫端只由 Grep 得知行號、未讀全文。

三次結論都與 `answer-key-v1.md` 的兩格錯答相反，推翻它的那一行是 `Reports/DependentReportController.cs:20`。

## 負對照（2026-09-20）

| run | 工具 | 提示 | 回合 | ms | USD | 回覆 | 引用 | 抽驗 |
|---|---|---|---|---|---|---|---|---|
| notools-1 | 無 | prompt.txt | 1 | 2,742 | 0.0270 | 假裝呼叫 Glob 的文字，無 JSON | 0 | — |
| notools-2 | 無 | prompt.txt | 1 | 2,214 | 0.0033 | 假裝呼叫 bash 的文字，無 JSON | 0 | — |
| guess-1 | 無 | prompt-guess.txt | 1 | 11,804 | 0.0172 | 完整 JSON，結論方向大致對 | 10 | 0 通過（檔案不存在） |
| guess-2 | 無 | prompt-guess.txt | 1 | 9,529 | 0.0104 | 完整 JSON | 10 | 0 通過（檔案不存在／行號超出 21 行） |

`run.ps1` 加 `-tools ''`（無工具）與 `-promptFile`；`check_citations.py` 對無 JSON 回覆印原文。

## 界線

教學示範 repo 只有 7 檔；真實系統呼叫鏈更長、命名更亂。三次一致不是統計。它答對是因為呼叫鏈就寫在程式裡，用工具能追到，不是因為它理解薪資。未驗證任何修法。
