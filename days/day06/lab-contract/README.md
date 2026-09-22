# Day 6｜欄位檢查的能力邊界

D-199 改稿新增的公開合成 .NET 測試，沒有呼叫模型。原始 Validate 函式從 [舊附件](../../v11/day04-10-dotnet/README.md)逐字複製；原附件及舊結果不改。

在本目錄執行 `dotnet run --project Demo.csproj`。首次需要 .NET 9 SDK 與套件還原。不要建立 deliberately-nonexistent-evidence.txt；測試會先確認其不存在。

[實際輸出](run.txt)｜[版本與函式雜湊](verification.json)｜[程式](Program.cs)

五項檢查通過表示預定的行為被重現：空證據與申報阻塞會被擋，但不存在的檔名仍通過結構檢查。這不是安全修復或正式流程完成；沒有重播 Day 4 任務。
