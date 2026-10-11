# 中斷重跑對照：Claude Code 做到一半被中斷，重開之後會不會再送一次？

Day 27 文中「五張訂單寄出八封」的完整紀錄，Day 28「基本功一：狀態放在外面」引用。

## 這裡有什麼

| 檔案 | 用途 |
|---|---|
| `criteria.md` | 跑前寫定的設定、量測與事前預期；跑後追加的結果 |
| `receiver.py` | 本機教學接收端：只以 `op_id` 去重，每個非重複請求都算一次生效，寫進 `effects.jsonl` |
| `tool_send.py.tmpl`、`tool_query.py.tmpl` | 給 Claude 的寄送與查詢工具範本 |
| `run.py` | 每組：啟動接收端 → Claude 寄通知 → 第 3 封生效時強制結束 → 用 `--resume` 或新工作階段重開 |
| `show.py` | 印出各組摘要 |
| `runs/20261010T001223Z/` | 正式六組；`runs/pilot-*` 是試跑，因工具註解洩漏答案而不計入 |

## 怎麼跑

需要 Python 3 與 Claude Code CLI（已登入）。六組合計約 US$0.15，約 5 分鐘。

```powershell
python run.py
python show.py
```

看 `runs/<時間>/<組>/summary.json` 的 `effects_per_event`：每個事件應該剛好 1 次。`sess-*-fresh` 組會看到 E1–E3 各 2 次。

## 界線

各組只跑一次，是現象示範，不是發生率。`event` 組證明的是「接收端以事件 ID 去重」這條約定在本機成立，不代表外部郵件或付款服務自動具備相同保證。工作目錄預設在 `C:\<AUTHOR>\d27-work`，換機器請改 `run.py` 的 `WORK`。
