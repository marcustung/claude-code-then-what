# ORD-142 取消規則改版（教學、未核准合併）

1. 可追溯：本次目標 specs/rules-v2.md BR01-04；改動 runs/tests/diff.patch 與 diff.patch。來源 885e521；設計 plan.md 與 design-input/。
2. 獨立證據：rules-v2 為指定教學目標，非正式公司批准。外層 runner 執行 dotnet run，紅 runs/tests/tests.txt、綠 runs/impl/tests.txt；邊界 runs/integration-01/report.json，原始 requests.json、payloads.json、logs.jsonl 可核。
3. 語意邊界：RefundRequested 僅旗標，不執行退款；通知 API 已存在，只驗轉發現況，通知契約未正式接受。
4. 影響：HTTP 回應、通知 payload、log；順序重送已驗，並行與重啟持久性未驗。核心規則變更要 Owner 接受。
5. 接受：本機技術檢查通過，業務接受仍待 Owner；未建立遠端 PR 或部署。

補件：diagrams/cancel.mmd 與 diagrams/sequence.mmd 描述本次正常路徑、前後旗標與限制。教學規格可供技術驗證，不是正式金流核准；沒有 Owner 接受紀錄。

更正第一次審查：runs/impl/tests.txt 確實存在，請用 Read 直接讀這個相對路徑（正斜線），不要從 Glob 無命中推論不存在。第一次工具使用 Windows 反斜線 pattern；根因尚未隔離驗證，不當成一般工具缺陷。
