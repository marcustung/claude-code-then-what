# Day 17：Skill 透過 Grafana MCP 查 Log

用同一份 r2 訂單服務產生新請求，讓 Claude 依方法查詢 Loki。全部是本機教學資料。

## 元件各做什麼

- 訂單 API：執行建立與取消，寫出結構化 Log。
- Python 接收端：收到真正 HTTP 通知後記錄 notification_received。
- Alloy：收集這兩端的 JSONL，不負責判斷是否送達。
- Loki：儲存 Log。Grafana：提供資料來源與查詢入口。
- Grafana MCP：把唯讀查詢工具交給 Claude Code。
- Skill：規定先查訂單、再查相同通知 ID 的接收端，留下狀態與缺件。
- verify-results.py：檢查保存的工具紀錄與輸出，並非請模型自己打分。

## 環境

本次 Windows、Python 3、.NET 9、Docker Desktop Linux containers、Claude Code 2.1.285；模型實際為 Sonnet 5.5。模型呼叫會使用 Claude 帳號額度，且把工作目錄內教學程式、設計、Skill 與查詢結果送到 Claude 服務。不要換成公司資料直接重跑。

Docker 只開本機 3217（Grafana）、3117（Loki）。Grafana 使用匿名 Viewer；這是本機 demo 設定，不能當成正式環境的認證設計。MCP 限唯讀工具，但資料存取範圍仍需服務端權限實作，提示中的範圍不是多租戶安全隔離。

## 啟動與產生資料

先啟動 Docker Desktop，在本目錄執行：

```powershell
docker pull grafana/grafana:12.0.2
docker pull grafana/loki:3.5.0
docker pull grafana/alloy:v1.8.3
docker pull grafana/mcp-grafana:latest
python run-demo.py prepare my-live-01
```

每次使用新的 run 名稱，不覆蓋既有實驗。prepare 會自動找到原專案或公開 repo 的 Day 16 r2 發布包，核對 package-manifest.json 與 report.json，再啟動服務、送出三筆真實取消請求。也可用 `--package <完整路徑>` 指定該包；它的同層需要 manifest 與 report，所在 lab-delivery 需要 day16-design-trace-01 的程式與設計。

腳本會生成隨機管理者密碼，只傳入本機容器，不寫進 repo。開啟 http://127.0.0.1:3217 即可查看 Grafana。prepare 結束時 API 與假接收端會停止，Docker 的查詢平台繼續運行，讓後續模型查剛產生的 Log。

鏡像版本見 compose.yaml；MCP 的 latest 在 prepare 時解析為實際 digest，保存於 runs/<名稱>/images.json，生成的 MCP 設定使用該 digest。日後 latest 可能不同，請先核對工具介面，不能把新環境當成原實驗。

## 讓 Claude 真正載入方法並查詢

```powershell
python probe-mcp.py my-live-01
python run-demo.py model my-live-01 complete --attempt r2
python run-demo.py model my-live-01 missing-receipts --attempt r2
python run-demo.py model my-live-01 query-failure --attempt r2
python verify-results.py my-live-01 --attempt r2
```

probe 只測 MCP 連線，不呼叫模型。三次 model 各開新 session，顯式載入 `plugin/skills/trace-notification/SKILL.md`，以 `day17-trace:trace-notification` 呼叫。這是為了在隔離的測試設定下確認載入，不宣稱一般專案 Skill 都必須包成 plugin。

run-demo.py 給模型 Read/Grep/Glob/Skill 與限定的 Grafana 唯讀工具；不給 shell 或寫入工具。每案最多 US$3，逾時七分鐘停止等待。MCP Docker 指令必須有 `--transport stdio`，不能沿用映像預設的 SSE 入口接 CLI stdio。

## 三案怎麼安排

| 案例 | 刻意安排 | 接收端預期 |
|---|---|---|
| complete | 兩端 Log 都收集 | confirmed，附相同通知 ID 接收紀錄 |
| missing-receipts | 實際有收到，但刻意不收集接收端 Log | unknown，不能判沒送到 |
| query-failure | 指定資料來源連向不可用位址，Grafana 回 502 | unknown，保留工具錯誤 |

工作目錄 workspaces/ 只有任務、兩個程式檔、設計、Skill 與 MCP 設定。audit/ 保存測試端真值，沒有作為模型輸入；feed/ 是送入 Alloy 的 Log。這是實驗輸入隔離，並非已證明對惡意模型的檔案系統沙箱。

每案 model/r2/ 保存 prompt、command、input-manifest、trace、tool-calls、tool-results、answer、result、execution。36 項檢查涵蓋三案各十二項，不代表 36 次獨立實驗；自然語言推論仍需逐項人工核對。

## 已保存結果與停止

參閱 [RESULTS.md](RESULTS.md)。不要對既有 run 重跑 prepare，也不要把舊時間窗改成今天後沿用旧結果。

停止這個 demo，不影響其他 Docker 專案：

```powershell
docker stop ironman-day17-logs-alloy-1 ironman-day17-logs-grafana-1 ironman-day17-logs-loki-1
```

這只停止容器，保留資料。此範例每次 prepare 會讓同一套 Alloy 改讀新 run，不支援同時跑兩輪 prepare。
