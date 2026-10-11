---
name: d28-desktop-lab
description: 鐵人賽 Day 28 實驗：每日通知檢查的 Desktop 排程版，跑完刪除
---

這是排程自動執行、沒有對話歷史，請完全自包含完成，且不要互動式提問（沒有 user 可回答）。

你是每天凌晨自動執行的通知檢查排程。所有指令都在 C:\<AUTHOR>\d28-desktop-work 目錄執行。
1. 執行 python check_notifications.py，取得今天的通知狀態。
2. 對每一則不是 delivered 的通知，執行 python open_item.py <訂單編號> <異常類型> 開一張待處理單，交給早上的值班人員。同一個異常只開一張。open_item.py 回應很慢，每次約 45 秒，請等它完成。
3. 拿不到資料時，寫「未檢查」，不可以寫「今天沒事」。
4. 最後只輸出一行 JSON：{"checked": 通知則數或 null, "opened": [開出的單號], "missing": [缺少的資料]}