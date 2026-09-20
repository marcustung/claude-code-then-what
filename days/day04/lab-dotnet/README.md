# Day 4–10｜.NET 公開教學附件

這是 2026-09-11 由 Codex 備稿建立的新教學示範，不是公司程式、歷史 patch 或 Claude 執行結果。沒有呼叫模型、外部業務系統或部署。

需要 .NET 9 SDK。本次環境 SDK 9.0.314。不需第三方 NuGet 套件。此為 console assertion 示範，不宣稱使用 xUnit 或公司測試框架。

```powershell
dotnet run --project Demo.csproj -- all
dotnet run --project Demo.csproj -- baseline
dotnet run --project Demo.csproj -- contract
dotnet run --project Demo.csproj -- bug
dotnet run --project Demo.csproj -- context
```

- Day 4：`bug` 配合再交付紀錄，展示缺少例外的修正。
- Day 5：`baseline`，合成人分鐘／經過分鐘分開。不能當公司效果。
- Day 6：`contract`，五種交付狀態與缺件檢查。只查欄位關係，不查檔案存在或內容真偽。

`run.txt` 保存實際工具輸出；`verification.md` 保存時間、指令、exit 與限制；`manifest.json` 保存本輪來源檔案 SHA-256，不包含自己。

五個 bug 情境：直接返回、缺授權、缺要求、合法重開、非拒絕。非拒絕通過只代表本 guard 不阻擋；正式系統仍需其他狀態檢查。

本包核心程式在 Program.cs。fix.diff 是對該判斷函式的教學節錄，不宣稱可直接 git apply 到公司專案。
