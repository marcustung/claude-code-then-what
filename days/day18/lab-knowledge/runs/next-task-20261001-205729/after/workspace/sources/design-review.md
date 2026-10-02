# 核對結果

1. API:69 呼叫 Domain，79 建通知、84 等待入列、88 日誌、89 回應；正常分支入列在回應前。Worker 的送達與 HTTP 回應沒有固定先後。原始圖順序不採用。
2. FakeSink 未保存 refund_requested 不等於 payload 未變。應用測試接收端觀察 payload；單看收據不足。原始「只影響兩個外部位置」不採用。
3. API 仍有 Shipped 的 HTTP 狀態判斷，不能寫成 API 完全沒有條件邏輯；本次保留退款計算在 Domain。
4. read/decide/write 非整體原子；個別 lock 不保證並行取消安全。
5. 檔案日誌不等於記憶體佇列。持久性限制針對訂單儲存與佇列，不把檔案說成必然重啟消失。
6. notification 決策表並非全部 proposed；有沿用項。本文只排除未接受的新提案。
7. 本輪未跑 .NET。新單元、HTTP、payload、順序重送均為待執行設計。
