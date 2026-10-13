# Day 29 長期實驗原件：LoopDeck 迴圈、長跑與外層評分

文章：Day 29｜排程都跑起來了，為什麼我反而更忙？

2026-10-05 起在本機跑的長期實驗。四條迴圈（l-01 通知重送、l-02 告警調整、l-03 Skill 優化、l-04 迴圈自我健康）和四條只出報告的對照組（r-01～r-04），由 LoopDeck 每天凌晨觀測、提案；Gate 1、Gate 2 由人裁決。另有「拿掉關卡、一路跑到達標」的長跑組。文章引用的「7 分鐘、US$0.69 就 11 項全綠」與那段越線的 diff，出自 `longrun/exp1-*`。

事前判準、對照設計與偏離紀錄（含三次靜默停擺）在 `protocol.md`：跑前寫定，跑後只在偏離紀錄追加。

## 這裡有什麼

| 路徑 | 內容 |
|---|---|
| `ws/` | LoopDeck 工作區：`config.yml`、`governance/`（目標、邊界、SSOT）、`issues/`（每條迴圈與每張提案的卡片、每輪 `runs/*.md` 與 `*.trace.jsonl`） |
| `ws-git-log.txt` | 工作區的 git 紀錄。LoopDeck 用 git 當資料庫：提案、狀態轉換、裁決都是一筆 commit |
| `order-service/main/` | 教學用訂單服務的主幹 |
| `order-service/branches/*.patch` | 每張提案（`ld/p-*`）與對照組報告（`ld/r-*`）各自的修改 |
| `order-service/git-log.txt` | 所有分支的 git 紀錄（含 Gate 2 合併） |
| `ops-grader/` | Claude 碰不到的外層：常駐時鐘 `clock.py`、每日出題與評分 `daily.py`／`simulate.py`／`evaluate.py`、Skill 每日考卷 `skill_daily.py` 與 `skill-eval/`、每天的指標與事故答案 `data/`、`clock.log` |
| `longrun/` | 長跑組：每次迭代的紀錄與 trace、`*-repo.patch`（它最後改了什麼）、`*-repo-log.txt` |
| `process-logs/` | 引擎與時鐘程序的 log；停擺期間沒有任何錯誤紀錄 |

## 界線

- LoopDeck 引擎本身不在這裡（開源版整理中）。
- trace 裡列出作者環境的紀錄行（工具、外掛、MCP、Skill 清單）已改成 `redacted`；email、本機路徑已去識別。每次 Skill 考卷的逐題暫存（84 MB）未收錄，成績在 `clock.log`。
- 部分 Gate 1 裁決（2026-10-06、10-07）由 Claude 代作者裁決，卡片意見前綴「（Claude 代 <AUTHOR> 裁決）」，分析人的裁決時不計。
- 實驗中斷三次（10-06、10-07、10-08～10-11），原因未查明；每條迴圈的樣本數很小，只示範現象，不估發生率。
