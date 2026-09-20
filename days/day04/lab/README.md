# Day 4 本機 POC

公開合成資料；無公司資料、無遠端 PR。使用 .NET 主控台斷言 runner（不是 xUnit 或 dotnet test）。原始結果位於 results/。

重跑：`node run.cjs`；重跑模型需 `node review.cjs`，會使用已登入的 Claude 服務。

CODEOWNERS 帳號為占位符，GitHub workflow 未遠端執行；不能證明合併阻擋。Claude 本機審查以相同契約輸入，並不等於 Claude Code Action 實跑。
