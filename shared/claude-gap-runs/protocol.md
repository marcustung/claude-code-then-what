# 預先固定實驗設計

2026-09-11，本次新實驗，公開合成任務，非歷史公司成果。

- Day 7：Claude Read 工具讀獨立理由卡；檢查 trace 確有 Read、標記 RULE-CONTEXT-7-KITE-0911、RULE-01、五情境決策與理由引用。這是明確讀檔，不測 CLAUDE.md 自動載入。
- 預先答案：[false,false,false,true,true]。檢查五個決策、RULE-01、是否辨認合法例外被錯擋。未知需承認缺少真實 auth、稽核等資料，不因回覆較長加分。保留所有輸出與失敗。
- 記錄實際回傳模型 ID；若不同則不可當同模型比較。沒有控制 temperature/seed，不宣稱 deterministic。
- Day 10：Claude 只產出修正 source；本地工具保存並由 Codex 執行 .NET before/after 驗证。模型不能執行工具，不冒稱 Claude 自己跑測試。
- Day 10 獨立檢查全部八種 boolean 組合；期待 !rejected || (reopenRequested && authorized)。保留 before failing exit、after exit、source diff 與 hash。
- 成功不能推論企業開發加速、人工減載或模型一般優勢。
