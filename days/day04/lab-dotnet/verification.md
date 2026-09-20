# 本輪驗證

- 日期：2026-09-11；.NET SDK 9.0.314。
- 指令（由專案根目錄）：`dotnet run --project ironman2026/artifacts/v11/day04-10-dotnet/Demo.csproj -- all`
- 最終工具 session：32397；輪詢完成 exit code 0。
- `run.txt` 為此次工具 stdout 原文保存，換行正規化為 LF。
- 13 項 console assertions 通過：1 項時間維度、5 項契約、5 項修正版情境、1 項原版重現、1 項 A/B 輸入差異。
- 原版合法重開情境的 FAIL 是預期缺陷重現；不代表最終檢查失敗。不是 13 項 xUnit 測試。
- 初次 sandbox run 因 NuGet.Config 讀取權限失敗；取得執行授權後完成。最終版本補齊 A/B 共同輸入中的函式與五個情境後重跑。
- 未執行 Claude／模型 A/B、公司測試、部署、使用者試用或工時觀察。
