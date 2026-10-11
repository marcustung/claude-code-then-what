# Day 28｜交給排程每天自己跑，我不在旁邊，Claude 靠得住嗎？

| 格 | 內容 |
|---|---|
| 文章 | 未發 |
| 今天練習 | 把每天凌晨的通知檢查交給排程（claude -p 模擬排程器八組＋真的 Desktop 排程 13 輪）：上一輪未完又觸發、同一異常出現兩次、沒給權限、資料源連續失敗，各會怎樣；鎖、去重與停止派送放在 Claude 外面 |
| 需要什麼 | Python 3；Claude Code CLI |
| 跑什麼 | `cd days/day28/lab-schedule; python run.py A1 A3 D` |
| 看什麼 | A1/items.json 有 4 張（重複）；A3/scheduler.jsonl 的 skipped；D/scheduler.jsonl 的 not_dispatched 與 handoff.md；各組 summary.json 的退出碼都是 0 |
| 範本 | [loop-contract.md](../../templates/loop-contract.md) |
| 原件 | days/day28/lab-schedule（criteria.md、service.py、run.py、runs）；days/day28/lab-desktop（Desktop 排程實測：criteria.md、task-prompt.md、stop_hook.py、runs）；days/day28/lab-interrupt（Day 27 提到的中斷重跑對照） |
| 界線 | 本機教學服務；鎖與停止派送是外層腳本邏輯，不是 Claude Code 內建；各組一次，只示範現象 |


[回 30 天索引](../../README.md)
