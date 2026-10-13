# Day 29 迷你迴圈：一份 YAML、兩百多行 Python，跑一圈第三階

文章：Day 29｜排程都跑起來了，為什麼我反而更忙？

給 Claude 一個目標（`improvement_goals`）和幾條不能越過的線（`constraints`），讓它自己觀測、自己提案；人只在兩道關卡做決定：Gate 1 這張提案值不值得做，Gate 2 做出來的修改收不收。題目是模擬訂單服務的告警調整。

## 這裡有什麼

| 檔案 | 用途 |
|---|---|
| `loop.yaml` | 契約：目標、邊界、可改的檔案、每輪花費上限、提案上限、連續失敗上限 |
| `loop.py` | 外層：`day`（產生當天指標並評分）、`observe`（Claude 只讀觀測、提案）、`implement`（Claude 在副本實作，外層檢查改動範圍、重播評分）；鎖、`STOP`、去重、提案上限都在這裡擋 |
| `decide.py` | 人的兩道關卡：`approve`、`reject`、`merge`、`policy-merge`、`list` |
| `grader/` | 模擬器與評分器。事故答案寫在 `grader/.truth/`，跑 `day` 時產生；Claude 的工作目錄在教學包外面，讀不到這裡 |
| `project/rules.yml` | 起始規則（5 條，全部 page、無持續時間） |
| `criteria.md` | 我那次實跑的事前判準與結果 |
| `my-run/` | 文章裡那一圈的完整紀錄：五張提案原文、每輪結果、裁決、最終規則、成績單 |

## 怎麼跑

需要 Python 3 與 Claude Code CLI（已登入）。一圈約 US$0.3。Claude 的工作副本預設放在教學包旁邊的 `mini-loop-work/`，可用環境變數 `MINI_LOOP_WORK` 改。

```powershell
python loop.py day 1                      # 第 1 天：應該是 page 雜訊 440、漏報 silent_drop
python loop.py observe --day 1            # Claude 觀測、提案 → proposals/
python decide.py list
python decide.py approve P-001 "理由"      # Gate 1
python decide.py reject P-002 "你的理由"   # 退回要寫理由，下一輪的提示會帶上
python loop.py implement P-001 --day 1    # Claude 實作 → 外層檢查只動 rules.yml → 重播
python decide.py merge P-001              # Gate 2
python loop.py day 2; python loop.py observe --day 2   # 看它怎麼回應你的退回理由
```

## 界線

Claude 每次提的提案不會和我那次一樣；各步只跑一次，示範現象，不估發生率。迷你版不是 LoopDeck 的完整實作（沒有排程器、lease、分支與看板）。

## 欄位命名更新

improvement_goals 表示改善目標，constraints 表示限制條件。僅更新目前教學程式與設定；my-run 中的原始實跑紀錄及歷史實驗使用舊名稱，保持原樣。
