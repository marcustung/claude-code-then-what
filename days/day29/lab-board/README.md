# Day 29 工作看板彙總：提案提出與裁決

文章「放大之後：為什麼我反而更忙」那張累計圖的資料。

- `board-proposals.json`：我真實工作看板上 30 張改善提案的時間軸，取自卡片狀態檔的 git 紀錄。卡片編號已改成 `card-01`～`card-30`，標題與內容不公開。欄位：`created` 提出日、`decided` 第一次離開待裁決的日期與去向（沒有表示從未裁決）、`now` 2026-10-11 的狀態。
- `plot_board_flow.py`：產圖腳本，`python plot_board_flow.py out.png`。

界線：只計改善提案；「裁決」＝Gate 1 第一次離開待裁決狀態；人工分鐘未記錄。
