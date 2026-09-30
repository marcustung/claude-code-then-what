# order-cancel-lifecycle 專案規則

RULES-TOKEN: oc-dev-r1

## 先讀
- 規則只以 `specs/rules-v2.md` 為準；`specs/decisions-v1.md`、`rules-v1.md` 是歷史。通知契約 `specs/notification-contract-v2.1.md` 是提案，本次開發不實作通知。
- 三個型別簽名不可改：`Order`、`CancellationResult`、`Cancellation.Cancel`。

## 做法
- 測試先行：先把要改／要加的場景寫進 `tests/DomainTests/Program.cs`，`dotnet run --project tests/DomainTests` 看到 FAIL，再改 `src/Domain/`。
- 最小 diff；不重排、不重新命名、不加依賴、不碰 `src/Api/`。
- 不連付款服務、不呼叫任何外部系統；`RefundRequested` 是記憶體旗標。
- 專案根目錄有 `freeze.json` 時只能讀、只能提建議，不能改檔。

## 回報
- 每個結論附 `檔案:行號`；沒讀到就寫「未讀到」。
- 完成時列出：改了哪些 SC、哪些測試從紅變綠、哪些沒動。
