# Day15 操作附件：同包壓測與本機 Grafana

正文見 Day15。以下為本機教學環境，不操作 Production。需要 Windows、Python 3、.NET 9、k6 1.3.0、Docker Desktop（Linux containers）；本次用 Prometheus 3.1.0、Grafana 12.0.2。

## 1. 先確認輸入

所有命令在專案根目錄執行。先有 Day14 的 `examples/sdlc-delivery/runs/candidate-checked/package` 及同層 `package-manifest.json`。若沒有，先依 Day14 操作附件建立自己的包與紀錄；不要把作者數字套在自己的版本上。

閱讀 `examples/sdlc-delivery/day15-lab/performance-test-plan.md`，確認情境、門檻與環境。教學門檻不是公司 SLA；改目標後另存計畫與新 run 名稱。

## 2. 啟動本機觀測

```powershell
docker compose -p ironman-day15 -f examples/sdlc-delivery/day15-lab/compose.yml up -d
python examples/sdlc-delivery/day15-lab/metrics_bridge.py
```

第二行會佔住終端機，另外開一個終端機執行測試。它在 `127.0.0.1:19115` 提供最新服務採樣，Docker 內的 Prometheus 透過 `host.docker.internal` 讀取。這是 Windows Docker Desktop 的本機連法；其他平台需要調整。

Grafana：`http://127.0.0.1:13015/d/day15-readiness`；Prometheus：`http://127.0.0.1:19095`。僅綁定 localhost，匿名只有 Grafana Viewer，不是遠端分發設定。測前確認這三個埠沒有被其他程式使用。

## 3. 分開跑三種情境

```powershell
python examples/sdlc-delivery/day15-lab/run-load.py my-smoke --profile smoke --k6 k6
python examples/sdlc-delivery/day15-lab/run-load.py my-spike --profile spike --k6 k6
python examples/sdlc-delivery/day15-lab/run-load.py my-sustain --profile sustain --k6 k6
```

必須依序執行，指標橋接目前只服務一輪測試。`k6` 不在 PATH 就改成完整路徑。run 名稱必須是新名稱；既有結果不覆寫。

每輪先核對十檔雜湊，再啟動發布包和固定回 200 的假接收端。結束後最多等二十秒對帳；服務退出、整輪超時、門檻失敗或通知不齊都不算通過。API 與假接收端由 runner 關閉，Grafana 與 Prometheus 保留供閱讀。

`load.js` 為 Claude Code 實際產生的腳本，`load-claude-original.js` 保留原始版本；之後僅補 `systemTags` 排除每張訂單的 URL 標籤。程式使用穩定端點名稱、testid 與 scenario 區分，不把 order ID 放進指標。

## 4. 看什麼檔案

| 檔案 | 回答什麼 |
|---|---|
| `report.json` | 包是否相同、k6 是否通過、通知 ID 是否一對一 |
| `k6-summary.json` | 實際請求數、首次取消 p95、失敗率、checks、dropped iterations |
| `k6-samples.json` | 逐筆原始測量，可重算與分情境 |
| `logs.jsonl`、`receipts.json` | 狀態轉換、送出紀錄與接收紀錄逐筆對帳 |
| `metrics-samples.json` | 每半秒的服務工作集、heap、GC、佇列採樣 |
| `article-summary.json` | 作者自原件整理的正文數字，原件仍保留 |

k6 1.3.0 舊格式摘要的 `thresholds` 布林值表示是否失敗，`false` 不等於「未通過」。Rate 類型的 `passes/fails` 是該布林事件真假次數；`http_req_failed` 的 `value=0` 才是本例失敗比例，不能把它的 `fails` 當失敗請求數。搭配 k6 結束碼、console 與原始樣本判讀。

Dashboard 的首次取消 p95 按 scenario 顯示累積彙總，並把 Remote Write 時間值由秒轉為毫秒；不平均不同群組的 p95。失敗率面板取標籤群組最大值，不宣稱整體加權失敗率。整輪結果用 k6 原始摘要。

工作集與 GC heap 是兩個不同數字；通知累計在服務重新啟動後歸零。採樣可能漏瞬間尖峰，沒有 CPU、鎖等待或完整 trace。Grafana 圖表不能取代通知 ID 的程式對帳。

## 5. 本次紀錄與已知問題

- `day15-smoke-01`：21 訂單／84 HTTP；p95 26.1344ms。k6 指標可用，但服務採樣轉送的 CRLF 讓 Prometheus 解析失敗；原始採樣仍保存。
- `day15-spike-01`：683／2,732；p95 18.05984ms。修正 LF 換行後服務指標接通。
- `day15-sustain-01`：1,201／4,804；p95 23.8399ms。三輪測試與通知對帳皆通過，未發生 Production 部署。
- 未設定 stale markers 的 k6 gauge 在測試停止後可能暫留最後值，不能當作新流量。用原始 run 時間界定。spike 舊 runner 結束後服務橋接也曾保留最後採樣；sustain 已改成停止時清空服務樣本。
- `claude-result.json` 保存 CLI 原始回覆；模型完成架構閱讀與腳本產生，本機執行器完成測試。沒有宣稱模型獨立部署 Docker 或產出量測後根因。
- 這是新增的三輪實驗，沒有覆寫早期 `acceptance-load-02` 或挪用其數據。

## 6. 關閉與保留

橋接終端機按 Ctrl+C，容器用：

```powershell
docker compose -p ironman-day15 -f examples/sdlc-delivery/day15-lab/compose.yml stop
```

此設定未配置持久化資料 volume；移除容器會失去其中的 Prometheus 歷史。原始 JSON、日誌與截圖另存專案，不依賴容器作唯一證據。

## 7. 選用：讓官方 Skills 協助制定策略

以下依官方文件整理，尚未在本文三輪實跑採用。前六節保留 k6 1.3.0 的重跑條件；不要為了版本一致改寫舊紀錄。使用新版本請另留版本、計畫、腳本與 run，不混用舊結果。

### 路線 A：k6 x agent

需要 k6 2.0 以上，從預計放壓測腳本的專案根目錄執行：

```powershell
k6 version
k6 x agent init --dry-run claude-code
k6 x agent init claude-code
k6 x agent status
```

先確認版本，`--dry-run` 預覽要建立或合併的檔案；確認後執行初始化，再看狀態。第一次使用子命令會取得擴充元件。Claude Code 的 Skills 放在 `.claude/skills/`，MCP 設定包含 `.mcp.json` 與 `.claude/settings.local.json`；檢查權限與目標環境後才執行測試。

| Skill | 用途 |
|---|---|
| `k6-test-planner` | 規劃策略與測試類型；需求、架構及風險仍由專案提供 |
| `k6-smoke-test` | 小負載確認操作、資料與檢查 |
| `k6-load-test` | 撰寫負載、壓力、尖峰與持續負載測試 |
| `k6-browser-test` | 瀏覽器操作與前端測試 |
| `k6-playwright-converter` | 將 Playwright 腳本轉為 k6/browser，仍須驗證轉換後行為 |

本案例以 planner → smoke → load 為使用順序，這是工作安排，不是三者已自動串成 pipeline。瀏覽器與 Playwright 轉換不是本輪 API 壓測必需。

### 路線 B：Grafana Skills plugin

這是另一條 Skills 入口，不必為了同一件事全部重複安裝；安裝 plugin 不等於完成前述 MCP 設定。

```powershell
claude plugin marketplace add grafana/skills
claude plugin install grafana-k6@grafana-skills
```

| Skill | 用途 | 環境 |
|---|---|---|
| `k6` | 產生、驗證與審查腳本 | 可用於本機 k6 |
| `k6-test-maintenance` | 維護腳本、版本遷移、服務改版後檢查 | 依實際專案與工具 |
| `k6-cloud-investigate-test` | 查特定測試的歷史、指標與 Log，調查結果 | Grafana Cloud k6 |
| `k6-trend-analysis` | 分析多輪指標漂移與門檻餘裕 | Grafana Cloud k6 |
| `k6-manage` | 透過 gcx 或 API 管理測試、執行與排程 | Grafana Cloud k6 |

本篇的本機 Grafana 並不是 Grafana Cloud k6，不能裝 Cloud Skill 就假定能查本機測試。門檻調整需要需求與理由；服務出錯時，不要藉由放寬 thresholds 把失敗變成成功。

### Skill、MCP 與實際執行

Skill 提供方法，Claude 依上下文使用；MCP 提供可呼叫工具；k6 實際執行測試。官方 `validate_script` 會以 1 VU、1 iteration、30 秒 timeout 進行驗證，會送出真實請求，不只是語法檢查。

`run_script` 回傳 stdout／stderr、退出碼與可取得的解析指標。目前文件列參數上限為 50 VUs、5 分鐘；這是該 MCP 工具的限制，不是 k6 的整體能力。較大或較長測試使用核准的 CLI／CI／Cloud 執行安排。本文 runner 還會管理發布包、假下游與通知對帳，不能用一次 MCP 呼叫就宣稱全部涵蓋。

### 要讓 Claude 先交回什麼

先提供需求、設計、Mermaid 架構圖、API、實際設定及已知流量資料。文件名稱可以不同，來源與版本要對得上。要求先交回：

1. 想解決的風險與尚缺資訊。
2. 每個情境對應的需求、模組與理由。
3. 負載方式、持續時間、量測來源及停止條件。
4. 門檻來源、待確認者與未驗範圍。

確認後再產生腳本、跑小負載、核對結果，再增加負載。Claude 提策略，人確認產品承諾與環境授權。下游失敗、長時間資料累積若未跑，仍列未驗。

若要在既有實驗上加入官方 Skill，先另開一輪「策略與腳本審查」，保存實際載入紀錄、原始回覆與修訂差異；有需要才重跑受影響情境。沒有發現也照實記錄，不能把文件介紹當模型實際參與。後續維運篇重用同條件測試驗修法，不再介紹一遍工具安裝。

## 8. 已完成的官方 planner 補測

原三輪没有使用官方 Skills；新增這輪只載入 `k6-test-planner`。來源固定在 `grafana/xk6-subcommand-agent` commit `99e22125a780dae3cbf74c2e1a130b1062a61305`，原文 SHA-256 `ee049cadde8560421fb0d90de7853cb1f014eb4ee4706bfc4226ff848a78f0a1`。

`examples/sdlc-delivery/day15-skill-lab/` 保存：

- `workspace/plugin/`：本機 plugin 包裝及未改動的官方 Skill。
- `workspace/brief.md`、`workspace/src/`：實際提供的教學需求與兩份程式。
- `records/manifest.json`：來源與輸入雜湊；`prompt.txt`、`command.json`：實際提示及命令。
- `records/trace.jsonl`：實際 Skill 呼叫與讀檔紀錄；`result.json`、`strategy.md`：模型結果。
- `records/original-plan.md`、`original-load.js`：事前保存、未提供給模型的原計畫與腳本。
- `predeclared-plan.md`：補測前確定的負載、延遲、觀察期限與通過條件。
- `load.js`、`run-load.py`：補測脚本與執行器。

Skill 由 `--plugin-dir` 載入，僅允許 Read、Grep、Glob、Skill。沒有 MCP，沒有 `k6 x agent init`，也沒由 Claude 執行負載。原執行腳本另存為 `run-planner-original.py`，裡面包含當時的暫存絕對路徑，屬歷史紀錄，不是可攜式入口。新環境可在 `workspace` 啟動 Claude，指定此 plugin，再使用保存的提示；模型輸出不保證相同。

策略採用預先建單、单獨量首次取消；作者另外選擇立即回應與延遲 300ms 的下游對照，並補上模型漏掉的通知接收紀錄核對。重跑用新名稱：

```powershell
python examples/sdlc-delivery/day15-skill-lab/run-load.py my-skill-control --profile control --k6 k6
python examples/sdlc-delivery/day15-skill-lab/run-load.py my-skill-slow --profile slow --k6 k6
```

需要既有 `runs/candidate-checked/package` 及其 manifest、.NET 9、Python、k6。本補測不需要 Prometheus 或 Grafana；保存本機原始樣本，未加入正文舊截圖。

每組先建立 210 張訂單，20 秒內每秒取消 10 張，最多 50 VUs。量測僅為首次取消延遲，建單不計入 `cancel_ms`；整體 HTTP 計數仍包含建單。實際各完成 201 次取消，不能把 210 當取消數。

結果：正常組 201 筆通知接收紀錄、p95 5.9854ms；慢下游組 127 筆通知接收紀錄、p95 13.3679ms。兩組 k6 exit 都是 0，但慢下游的整體 runner exit 為 1，因為在負載後最多二十秒的觀察期限內，通知 ID 對帳未完成。74 筆未有通知接收紀錄不等於永久遺失，截止時即停止本次服務。

慢下游關閉服務時，尚在處理的假接收端出現連線重設訊息，發生在結果快照後，不能算成負載期 HTTP 失敗。planner 外層腳本也曾因終端機 CP950 無法印出 Unicode 而 exit 1；Claude 子程序 exit 0、結果已完整保存，沒有為了終端顯示而重跑或挑選模型結果。

本次兩組單次對照不能證明 Skill 優於不用 Skill，也不是正式容量或 SLA 驗證。原始歷史結果未覆寫。

## 延伸閱讀

- [壓測投影片：超越監控，Grafana K6 帶你探索應用程式的深淵](https://speakerdeck.com/marcustung/chao-yue-jian-kong-grafana-k6-dai-ni-tan-suo-ying-yong-cheng-shi-de-shen-yuan)
- [k6 Remote Write](https://grafana.com/docs/k6/latest/results-output/real-time/prometheus-remote-write/)
- [k6 Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/)

- [k6 x agent 官方設定](https://grafana.com/docs/k6/latest/set-up/configure-ai-assistant/bootstrap-with-k6-x-agent/)
- [k6 MCP 工具](https://grafana.com/docs/k6/latest/set-up/configure-ai-assistant/tools-prompts-resources/)
- [Grafana Skills](https://github.com/grafana/skills)


## 模型執行資料補充

原三輪腳本生成：一次 Claude 呼叫，約131秒，費用估值US$0.38。官方 planner 補測：模型回合耗時81.256秒，7回合，費用估值US$0.1349858。這些是個別呼叫資料，不是人工省時或工具優劣比較。planner 透過本機 plugin 包裝載入固定版本原文，未使用 MCP，也未執行 Skill 要求的文件查詢步驟。


## 追加唯讀診斷：已重跑並核對

首次 `day15-skill-lab/diagnosis-01` 因429／使用額度限制未取得分析，原件保留。重跑另存 `diagnosis-02`，輸入檔案雜湊與第一次完全相同，使用相同提示與Read/Grep/Glob唯讀工具；沒有MCP、寫入或執行工具。

重跑成功：模型耗時62.972秒，17回合，費用估值US$0.210347。`records/trace.jsonl` 保存讀檔與搜尋，`analysis.md`為原始分析，`verification.md`為後續核對。未修改服務、未新增壓測。

確認引用的Program.cs 87–92、224–246、258–259行可支持API先回應、背景逐筆等待HTTP、成功後記錄送出的路徑。模型的「阻塞」在正文改為等待HTTP結果，不代表阻塞執行緒。「API門檻不受延遲影響」不採用作普遍結論：只支持本次門檻通過，佇列累積仍可能間接影響資源與延遲。

模型僅抽樣讀取接收紀錄，不能宣稱其完成全量ID對帳。另以程式核對慢下游：201次轉換，127筆接收與127筆sent的ID一致且無重複，74筆轉換未有接收。最後20筆sent間隔約0.303–0.361秒，並非模型所寫穩定0.30–0.31秒。未完成不等於永久遺失；關閉與截止的精確事件時間仍未補記，沒有宣稱剩餘通知的最終狀態。

重跑方法：複製同一workspace至新目錄，保留empty-mcp.json與run.py，再執行run.py。它只對複製的教學輸入呼叫Claude服務，會產生使用費用；records已存在時會停止，不覆寫歷史結果。新模型回覆仍需核對，不能預期逐字相同。
