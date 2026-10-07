# Day 24：從規格補觀測，讓 Claude 查得到背景通知

這份範例回答：取消 API 已回應，通知卻晚了幾秒，等待發生在哪裡？先補觀測，再讓 Claude 用工具與程式核對。這是獨立 .NET 教學副本，沒有改通知功能，也不是 Production 環境。

## 先看哪裡

| 想做什麼 | 入口 | 看完應能確認什麼 |
|---|---|---|
| 看實際改動 | [API 程式](after/src/Api/Program.cs)、[OTel 設定](after/src/Api/Obs.cs)、[接收端](after/src/FakeSink/Program.cs) | Notification 保存關聯與計時起點，worker 接回 Trace，兩端分別留 Log |
| 先看既有結果 | [四輪摘要](runs/20261007-050642/summary.json)、[獨立核對](runs/20261007-050642/recheck/result.json) | 正常與慢下游在觀測前後都收到九筆，沒有重複通知 |
| 查關聯是否真的成立 | [初次驗證與 span](runs/20261007-050642/verification.json)、[後端原始回傳](runs/20261007-050642/backend) | API、worker、HTTP client、接收端的 parent 關係及等待時間 |
| 看 Claude 實際做了什麼 | [提示](runs/20261007-050642/claude/prompt.txt)、[工具紀錄](runs/20261007-050642/claude/tool-audit.jsonl)、[回答](runs/20261007-050642/claude/answer.md) | 查詢失敗如何處理，哪些是觀察、推論或未知 |
| 自己重跑 | 下方四步 | 產生自己的時間窗與原件，不覆蓋文章那一輪 |

## 這輪實際結果

原件在 `runs/20261007-050642`。正常與接收端延遲 250 ms，觀測修改前後各一輪，每輪九筆取消，都收到九筆；重複取消不多發通知。

`after-slow-8`：API 1.5909 ms、排隊 2186.6189 ms、下游 266.1336 ms、worker 268.9615 ms。worker span 不包含排隊；下游 client span 包含接收端 server span，不能把所有欄位相加。

Claude 透過自訂唯讀 MCP 呼叫 gcx 十次，八次成功、兩次非零退出；輸出過長另造成可見性限制。它只完整拆解一筆慢通知，不是所有 Trace 都由模型驗完。

## 在自己的電腦怎麼跑

本輪使用 Windows、Docker Desktop Linux containers、.NET 9 SDK、Python 3 與 gcx。現有 `run.py` 使用 Windows 子程序旗標，其他作業系統需先調整，尚未驗證。最後一步另外需要可用的 Claude Code 與本機登入。

下載時保留整個 Day 24 目錄：操作腳本在 `lab-observability`，旁邊的 `order-cancel-lifecycle` 放核對原始版本需要的程式與通知契約。私人工作區的對應目錄是 `examples/day24-observability-lab` 與 `examples/order-cancel-lifecycle`。不要只下載一支腳本。

在本範例目錄依序執行：

```powershell
python setup.py
python run.py
python verify.py
python run-claude.py
```

| 步驟 | 實際用途 | 會得到什麼 |
|---|---|---|
| `setup.py` | 啟動本機 LGTM，建立只讀取資料的 Viewer 帳號與 24 小時 token | Grafana 位於 `http://127.0.0.1:3224`；私人 gcx 設定留在 TEMP |
| `run.py` | 建置 before／after，跑正常與 250 ms 慢下游四輪 | 新的 `runs/<批次>/summary.json`、每輪請求、接收紀錄與 Log；`latest-run.txt` 指向這一輪 |
| `verify.py` | 直接查後端，核對接收 ID、Trace 父子關係與原始程式 | `recheck/result.json`；四個固定核對項目為 PASS 才算通過 |
| `run-claude.py` | 給 Claude 時間窗、服務名稱與程式，透過唯讀介面查資料 | `claude/prompt.txt`、`trace.jsonl`、`tool-audit.jsonl`、`execution.json` |

前三步可先驗環境與服務，不需要呼叫 Claude。最後一步會使用 Claude 額度並傳送教學資料。`execution.json` 的 exit code 只能說命令如何結束，不能代替結果核對。新一輪的回答在 `trace.jsonl`；歷史 `answer.md` 是另外整理的閱讀版，不是 runner 自動產生的檔名。

先在 Grafana Explore 選 Loki，使用 `summary.json` 的起訖時間與對應服務名稱查接收端事件。從事件取 `trace_id`，再到 Tempo 查同一條 Trace。這些 ID 每次會變，不能把文章那一輪的 ID 直接用在新一輪。

## 工具設定：唯讀 MCP 怎麼接

`run-claude.py` 會在本輪工作目錄寫一份 `mcp.json`，以 `--mcp-config` 掛上 `observability` 伺服器（`gcx_readonly_mcp.py`），並用 `--strict-mcp-config` 只載入它：

```json
{"mcpServers": {"observability": {"command": "python", "args": ["gcx_readonly_mcp.py"]}}}
```

| 限制 | 設定 |
|---|---|
| 內建工具 | `--tools Read,Grep,Glob`，沒有 shell、沒有寫入 |
| 額外放行 | `--allowedTools` 只多放行 `mcp__observability__query_observability` |
| `operation` | 只能是 `datasources`、`logs`、`metrics`、`trace_search`、`trace_get` |
| `datasource` | 只能是 `loki`、`prometheus`、`tempo`；另有故意不存在的 `missing-receiver-demo`，用來驗查詢錯誤 |
| Grafana 帳號 | Viewer，只讀本機教學環境 |
| 稽核 | 每次查詢寫入本輪的 `tool-audit.jsonl` |

介面內部以參數陣列呼叫 gcx，例如查慢情境的接收端紀錄：

```powershell
gcx logs query -d loki --expr '{service_name="day24-fakesink-slow"} |= "notification_received"' --from "<本次開始時間，UTC>" --to "<本次結束時間，UTC>" -o json
```

重點看 `--expr` 那一段：先限定接收端，再找 `notification_received`。`-d` 指定資料來源，`service_name` 限定接收端，時間窗取自本輪執行紀錄。這裡的時間是佔位文字，重跑時要換成自己的時間。取得 Log 中的 `trace_id` 後，再以 `gcx traces get -d tempo <trace_id> --llm` 讀那一條 Trace。

這是自訂介面，不是官方 Grafana MCP server。

## 怎麼確認工具已準備好

1. `setup.py` 顯示 Ready，只代表本機環境與登入設定就緒。
2. `run.py` 留下四輪結果，再由 `verify.py` 確認兩組共十八筆接收 ID 確實進入 Loki、慢通知的非同步 Trace 接得起來。
3. 最後才看 Claude 的工具呼叫與回答，對照原始回傳，確認它沒有把查詢錯誤或空結果當成通知沒送達。

服務、蒐集器與模型三個層次要分開看。這次提示指定了部分查詢任務與缺資料檢查，驗的是環境與觀測是否可用，不是未知事故的盲測或一般診斷準確率。

## 常見停下來的位置

- Docker 尚未就緒或連線失敗：先處理環境，不能沿用舊結果當作新一輪成功。
- 5124／5125 被占用：`run.py` 會停止，不會殺掉別的服務。
- token 過期：重新執行 `setup.py` 取得新的暫時設定，不把 token 寫進 repo。
- 後端尚未收齊：`verify.py` 應失敗，確認匯出狀態後再查，不把缺資料補成 PASS。
- 已有模型軌跡：`run-claude.py` 拒絕覆蓋；要另跑服務建立新批次。

## 檔案與資料界線

- [before](before) 為原始程式副本；[after](after) 新增 OTel、跨背景工作的 ActivityContext、等待時間與集中 Log。兩份 Domain 程式相同。
- [gcx_readonly_mcp.py](gcx_readonly_mcp.py) 是自訂介面，非官方 Grafana MCP。只允許固定查詢與來源，不開放任意 shell 或修改操作。
- 等待時間從建立通知、準備入佇列時起算；重排保留起點，但本輪未開重排故障。
- 原版有本機 JSONL。集中後端回空不代表沒執行；`missing-receiver-demo` 來源不存在也不代表漏通知。
- 埋點由備稿工程工作完成；Claude 可核對的參與是工具查詢、讀程式與判斷。
- 每個條件只有一輪，沒有人工時間或 SLA 承諾；不外推容量、省時、Production 或診斷準確率。使用記憶體儲存、單 worker、教學接收端。

完成後可執行 `docker stop day24-lgtm`，保留容器資料。教學帳密 `admin/admin` 只用於 localhost；不要對外開放服務。

## 參考與公開狀態

- [From Observability to Observability Driven Development](https://speakerdeck.com/marcustung/from-observability-to-observability-driven-development)：觀測需求如何進入開發流程。
- [o11y-bench](https://github.com/grafana/o11y-bench)：觀測任務、工具環境與評估方法。
- [Claude Code MCP](https://code.claude.com/docs/en/mcp)：模型與外部工具的介面。

本機已整理操作、程式與原件，尚未推送 GitHub。公開副本只去識別本機路徑，原始實跑檔案不修改；不打包 bin、obj、私人設定或本機 mcp.json。發布前仍需沿用系列的統一打包與連結檢查。
