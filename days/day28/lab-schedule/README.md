# Day 28 排程實驗：同一個查核任務定期跑，重疊、重複、空跑、連續失敗時會怎樣？

文章：Day 28｜我不在旁邊，Claude 還能把維運工作接下去嗎？

## 這裡有什麼

| 檔案 | 用途 |
|---|---|
| `criteria.md` | 跑前寫定的問題、各組設定、事前預期；跑後追加的結果與判準沒涵蓋的觀察 |
| `service.py` | 本機教學服務：同時是通知資料源（`GET /notifications`）與待處理事項系統（`POST /items`，`new` 或 `dedupe` 模式）；所有請求寫進 `requests.jsonl` |
| `tool_check.py.tmpl`、`tool_open.py.tmpl` | 給 Claude 的兩支工具範本（唯讀查詢；開事項，故意慢 20 秒） |
| `run.py` | 模擬排程器：每次觸發開一個新工作目錄、一個新的 `claude -p` 工作階段；鎖（A3）與停止派送（D）都在這裡，不是 Claude Code 內建 |
| `figures/plot_overlap.py` | 重疊三組的時間軸圖 |
| `runs/20261010T162938Z/` | 文章引用的那一次實跑 |

## 怎麼跑

需要 Python 3 與 Claude Code CLI（已登入）。每組約 US$0.01–0.04，全部八組約 US$0.17、1–2 分鐘。

```powershell
python run.py            # 全部八組
python run.py A1 A3 D    # 只跑指定組
```

結果寫到 `runs/<時間>/<組>/`：

- `items.json`：事項系統實際開了幾張（A1 應該是 4 張，A2、A3 是 2 張）。
- `requests.jsonl`：服務端收到的每個請求，含是哪一輪發的。
- `scheduler.jsonl`：排程器的決定（`dispatched`、`skipped`、`not_dispatched`、`stop_written`）。
- `r1.trace.jsonl`：Claude 的工具軌跡；`summary.json` 有退出碼、`is_error`、`permission_denials` 與 Claude 最後的回覆。
- D 組另有 `STOP` 與 `handoff.md`（交回人紀錄）。

## 讀法與界線

- 驗收以服務端紀錄為準，不採信 Claude 自述。
- 各組只跑一次，是現象示範，不是發生率；模型會變，重跑結果可能不同。
- `dedupe` 只證明「事項系統以訂單＋異常類型去重」這條約定在本機成立，不代表任何真實工單系統內建相同保證。
- 工作目錄預設在 `C:\<AUTHOR>\d28-work`，換機器請改 `run.py` 的 `WORK`。
