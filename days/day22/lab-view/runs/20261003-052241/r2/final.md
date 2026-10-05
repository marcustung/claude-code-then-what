清單已寫入 `out/worklist.json`，共 6 件，31 筆結果全部歸入其中，今天處理 5 件。`results/` 沒有任何改動。

**怎麼分組**
31 筆都是同一張訂單、同一個 notification_id，只是情境不同。我先依情境分組，再看固定檢查器的狀態。

1. **decoy-receipt（14–22，共 9 筆）：** 收據的 id 是 `3f1c9a7e…`，和發送紀錄的 `7e746d20…` 對不上。它們的結論一致，所以合併成一件，由服務 Owner 向接收端查證。
2. **missing-receipts（02、23–31，共 10 筆）：** 缺 receipts.json，接收端狀態是 unknown。合併成一件，由服務 Owner 取得收據。
3. **complete 且固定檢查通過（01、11、12、13）：** 發送端與接收端都是 confirmed。合併成一件，由服務 Owner 人工核對。
4. **03：** 這筆沒有真的跑 gate.py，evidence_refs 是人工推得的。不能當作檢查通過，由查核者在能跑 Python 的環境重跑。
5. **04：** Skill 只有 SKILL.md，沒有 collect.py 和 gate.py，無法執行。由 Skill 維護者補齊。
6. **complete 的 05–10（不帶 Skill 或 v1）：** 固定檢查全數退回，原因是 UNKNOWN_SOURCE_REF 和 CONFIRMED_WITH_MISSING_SOURCE。我不採用這 6 筆的 confirmed 結論，也不逐筆重跑。這件今天不處理（false），由 Skill 維護者之後記錄 v1 的失敗模式。

**unknown 怎麼處理**
我沒有把 unknown 當成「未送達」或「已送達」，維持原狀，並要求取得對應收據後才改狀態。所有項目都維持「不補送、不結案」。

**要注意的地方**
- 同一個 notification_id 在不同情境下，接收端有的是 confirmed，有的是 unknown，兩者不可能同時為真。我當成各自獨立的測試資料包處理。如果其實是同一次真實通知，要先釐清是哪份資料。
- complete 那件的核對只涵蓋本機教學資料。.NET 的 payload 與重送測試沒跑過，也沒有正式環境的 Log server 資料。
- 「誰接」只能填三種角色，所以「人工核對」我歸給服務 Owner。如果你們實際是由查核者核對，改一個欄位就行。