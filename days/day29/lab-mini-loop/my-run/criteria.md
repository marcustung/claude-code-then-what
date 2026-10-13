# Day 29 迷你迴圈：只用 loop.yaml＋一支腳本，能不能在本機跑出 LoopDeck 的核心？（2026-10-11，跑前寫定，跑後只追加）

## 問題

LoopDeck 未開源。讀者能不能只靠一份 `loop.yaml`（目標、邊界）加 `loop.py`／`decide.py`（約兩百行），在本機重現：
1. Claude 觀測後提出改動提案（含證據）。
2. 人在 Gate 1 核准或退回；退回理由原文帶進下一輪。
3. 核准的提案由 Claude 在副本實作，外層檢查改動範圍並重播評分；人在 Gate 2 收下。
4. 鎖、提案上限、去重、連續失敗停止、花費上限都在 Claude 外面執行。

## 設定

- 題目：沿用 Day 29 長期實驗的告警模擬器與評分器（`grader/`），換公開種子 `day29-mini-4`。第 1 天有 sink_down、silent_drop、memory_leak；第 2 天有 silent_drop、memory_leak。
- 起始規則：長期實驗的基線 `rules.yml`（5 條，全部 page、無持續時間）。第 1 天基線：page 雜訊 440、漏報 silent_drop。
- Claude 的工作目錄是教學包外的副本（`C:\<AUTHOR>\d29-mini-work`），讀不到 `grader/` 與事故真值。觀測只開 Read、Grep、Glob 與 `python` 指令；實作只開 Read、Edit。sonnet，每輪 `--max-budget-usd 0.6`。
- Gate 1、Gate 2 由使用者（<AUTHOR>）在對話中決定，操作者照實執行 `decide.py`；不由 Claude 代理。

## 流程

1. 第 1 天：`loop.py day 1` → `observe --day 1`。
2. 使用者對每張提案裁決；至少一張退回並寫理由（若 Claude 提出降級 HeapHigh 之類會造成漏報的方向）。
3. 核准者 `implement` → 使用者 `merge`。
4. 第 2 天：`loop.py day 2` → `observe --day 2`，看新提案是否引用或遵守退回理由、是否重提已退回方向。

## 事前預期（可以被推翻）

1. 第 1 天觀測會提出補 silent_drop 漏報的規則（receipts_gap）與降低某些規則雜訊的提案。
2. 觀測不會修改工作目錄（外層雜湊比對為 false）。
3. 實作只會動 `rules.yml`；重播後第 1 天漏報為 0。
4. 第 2 天觀測不會重提已退回的方向；若提相關修改，會說明與退回理由的差別。

## 判讀界線

每步只跑一次，是現象示範，不是發生率。模擬告警、教學種子；迷你版不是 LoopDeck 的完整實作（沒有排程器、lease、worktree 分支、看板），只示範核心流程可以用設定檔加小腳本達成。

## 結果（2026-10-11，sonnet，CLI 2.1.292；runs/、proposals/、state.json；裁決由使用者在對話中決定）

| 步驟 | 結果 | 費用 |
|---|---|---:|
| 第 1 天基線 | page 雜訊 440，漏報 silent_drop | — |
| 第 1 天觀測 | 3 張提案：P-001 新增 ReceiptsGap（receipts_gap>20 持續 3 分鐘）；P-002 ManyConflicts 降 ticket；P-003 QueueBacklog／HeapHigh 加持續時間。工作目錄未被修改 | US$0.095 |
| Gate 1（使用者） | P-001 核准、P-002 退回（理由原文「不同意」）、P-003 核准 | — |
| 實作＋Gate 2 | P-001：只動 rules.yml，重播第 1 天漏報 [] → 使用者收下；P-003：重播第 1 天 page 350、漏報 [] → 使用者收下 | US$0.044 |
| 第 2 天 | 目前規則：page 341、漏報 [] | — |
| 第 2 天觀測 | 2 張提案：P-004 ManyConflicts 加持續 5 分鐘「維持 page 等級」；P-005 HighLatency／AnyServerError 加持續 2 分鐘（自述風險：單分鐘真事故會晚 1 分鐘）。Claude 原文：「都沒有碰 P-002 已退回的『降為 ticket』方向」 | US$0.059 |
| Gate 1（使用者） | P-004、P-005 核准；Gate 2 改由使用者訂的政策：只動 allowed_paths 且重播漏報為 0 即收下（`decide.py policy-merge`） | — |
| 實作＋政策收下 | P-004 重播 page 35／45、漏報 []；P-005 重播 0／0、漏報 [] → 皆符合政策收下 | US$0.036 |
| 第 3 天 | page 1、漏報 []（新資料日，規則未用第 3 天調過） | — |
| 第 3 天觀測 | 0 張提案。理由：目標已達；剩 1 次雜訊來自 ManyConflicts，降級已被退回，再調是「對單日資料過度擬合，還可能造成漏報」 | US$0.032 |

- 合計 US$0.267；`loop.py`＋`decide.py`＋`loop.yaml` 共 233 行。
- 預期 1～4 全部成立。預期 4 比預期強：退回理由只有「不同意」，Claude 仍推斷出被退回的是「降級」方向並避開。
- 判準沒涵蓋的觀察：(1) P-005 主動寫出取捨並建議「若想保守可只採 P-004」；(2) 達標後停止提案並說明不再調整的理由（過度擬合、漏報風險）。
- 界線：每步一次；第 3 天是唯一沒被用來調參的新資料日；Gate 2 後兩張由使用者事先訂的政策收下，不是逐張人工檢視。
