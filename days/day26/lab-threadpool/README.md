# Day26 ThreadPool starvation 教學實驗

先讀 [比較報告](REPORT.md) 與 [事前條件](criteria.md)。這是以訂單服務為背景的新故障注入，不是歷史公司事故還原；已完成 Claude 查因與兩版修復，最新結果見 [Claude 驗證報告](CLAUDE-VERIFICATION.md)。

## 重跑

Windows、.NET9 SDK、Python3。只綁127.0.0.1。以下從本實驗目錄執行：

```powershell
# 堆疊工具安裝在使用者目錄，不改全域工具。
dotnet tool install dotnet-stack --version 9.0.661903 --tool-path "$env:USERPROFILE/day26-diagnostics-tools"
python prepare.py
dotnet build service/src/Api/Api.csproj -c Release
dotnet build service/src/FakeSink/FakeSink.csproj -c Release
python run.py
```

prepare.py只更新本教學副本，不修改來源；若已自行改教學副本，先保留再重新prepare。每輪使用同一組件與新程序，LAB_WAIT_MODE切換等待路徑；client timeout30秒。取堆疊的第五輪與四轮計時比較分開。程序在finally清理，結果寫入新的UTC時間戳目錄，latest.txt指向最近一輪。

沒有CPU配額、没有修改ThreadPool上限，只有DOTNET_PROCESSOR_COUNT=2的runtime提示。以上命令重跑的是初始受控對照，並非 Claude 修復流程。後續 Grafana 重放、Claude MCP 查因與修復回歸，另見最新驗證報告；保留兩批來源，不混用。

## 不呼叫模型，重跑最終修法

從 repo 根目錄執行（Windows、Python 3、.NET 9 SDK）：

```powershell
python examples/day26-threadpool-lab/validate_claude_repair.py --workspace examples/day26-threadpool-lab/claude-final-source
```

會建置封存的 API 與接收端，用兩輪 384 張訂單、96 併發加同單 16 併發驗證。只綁本機隨機埠，完成後清理程序；結果在新的 repair-validation 時戳目錄，不覆蓋原件。這個入口不需要 Claude、Grafana 或私人暫存目錄。讀 summary.json 檢查 checks，再看 same-order.json 確認 16 個回應與 1 筆通知。負載結果會依機器而異，不能要求延遲精確等於本文。
