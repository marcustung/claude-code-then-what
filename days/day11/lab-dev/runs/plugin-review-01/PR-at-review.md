# ORD-142 取消規則改版（教學、未核准合併）

1. 可追溯：本次目標 specs/rules-v2.md BR01-04；改動 runs/tests/diff.patch 與 diff.patch。來源 885e521；設計 plan.md 與 design-input/。
2. 獨立證據：rules-v2 為指定教學目標，非正式公司批准。外層 runner 執行 dotnet run，紅 runs/tests/tests.txt、綠 runs/impl/tests.txt；邊界 runs/integration-01/report.json，原始 requests.json、payloads.json、logs.jsonl 可核。
3. 語意邊界：RefundRequested 僅旗標，不執行退款；通知 API 已存在，只驗轉發現況，通知契約未正式接受。
4. 影響：HTTP 回應、通知 payload、log；順序重送已驗，並行與重啟持久性未驗。核心規則變更要 Owner 接受。
5. 接受：本機技術檢查通過，業務接受仍待 Owner；未建立遠端 PR 或部署。

缺件：本次前後狀態／循序圖尚未附。不要靠測試綠燈替它補成有。
