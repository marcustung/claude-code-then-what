# ORD-142 v2 專案規則

RULES-TOKEN: ord142-v2-r1

## 先讀
- 動手前先讀完 `ticket/ORD-142-v2/02-RULES.md`；規則只以該檔為準，`decisions-v1.md` 是歷史。
- 三個型別簽名不可改：`Order`、`CancellationResult`、`Cancellation.Cancel`。

## 做法
- 測試先行：先把要改／要加的場景寫進 `tests/Program.cs`，`dotnet run` 看到 FAIL，再改 `src/`。
- 每次改動最小 diff；不要順手重排、重新命名、加依賴。
- 不連付款服務、不呼叫任何外部系統；`RefundRequested` 是記憶體旗標。
- 專案根目錄有 `freeze.json` 時只能讀、只能提建議，不能改檔。

## 回報
- 每個結論附 `檔案:行號`；沒讀到就寫「未讀到」。
- 完成時列出：改了哪些 SC、哪些測試從紅變綠、哪些沒動。
