# Day 26：第三方題庫成績（由 export.py 依本目錄檔案產生）

題目不是作者出的：從 [RCAEval](https://github.com/phamquiluan/RCAEval)（MIT）與 [o11y-bench](https://github.com/grafana/o11y-bench)（AGPL-3.0）各選 20 題，每題讓 Claude Code（sonnet）跑兩次。
本目錄只放成績：RCAEval 每次的 `result.json`（答案、正解、秒數、費用、回合）與 `final.md`（Claude 的回答）；o11y-bench 每次的 `result.json`（官方判分）。
o11y-bench 的題目、評分準則與執行紀錄不在這裡（授權與個人資訊考量），題目請到官方 repo 取得。`selection.json` 是選題清單。

## RCAEval（20 題 × 2 次，sonnet；第一名猜中根因服務才算對）

| 子類 | 答對 | 次數 |
|---|---:|---:|
| RE2-OB | 10 | 10 |
| RE2-SS | 9 | 10 |
| RE3-OB | 8 | 8 |
| RE3-SS | 6 | 6 |
| RE3-TT | 6 | 6 |
| 合計 | 39 | 40 |

前三名有正解：40／40；平均每次 66 秒、US$0.161。

## o11y-bench（20 題 × 2 次，sonnet；官方判分，分數是評分平均，滿分 1，不是答對率）

| 組別 | 全部 | 調查題 | 次數 |
|---|---:|---:|---:|
| base | 0.762 | 0.680 | 40 |
| mod-v02 | 0.699 | 0.667 | 40 |
| stoponly | 0.768 | 0.761 | 40 |

- base：一般工具流程；mod-v02：加查證清單與收工檢查；stoponly：只留收工檢查。詳見 O11Y-MOD-COMPARISON.md。
- 限制：單一模型；每題兩次；o11y-bench 每次重新產生遙測資料；保留組曾看過部分失敗內容。題庫成績不是診斷正確率。
