# 本次教學開發計畫

接 Day9 scope 與 Day10 設計核對。規格目標 specs/rules-v2.md，不是正式公司核准。
1. 只改 tests/DomainTests/Program.cs，SC01-07 對回規格，先對舊 Domain 執行。
2. 只改 src/Domain/Cancellation.cs，維持公開介面、不碰API、不接金流，讓規格場景通過。
3. 檢查 HTTP 回應、log、送往測試接收端的 payload；順序重送不能新增通知。這是既有API轉發的技術檢查，不是通知提案正式接受。
4. 對 diff 套用 Day4 原 review-kit，保留 owner-required；政策程式另查，模型不能解除。
5. 同一驗證入口產出 artifact、hash、預期與結果；本機封裝與啟動，不冒充遠端CI或正式部署。
6. 交付 runbook、未決與工作紀錄。人工分鐘未知，不補零、不推估省時。
