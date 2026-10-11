# Day 28 Desktop 排程實測：權限、重疊、hook 煞車

文章：Day 28｜交給排程每天自己跑，我不在旁邊，Claude 靠得住嗎？

把 `../lab-schedule` 的通知檢查放進 Claude Desktop 的本機排程任務，每分鐘觸發一次，看三件事：沒放行權限會怎樣、上一輪沒跑完會怎樣、`STOP` 煞車放得進去嗎。

## 這裡有什麼

| 檔案 | 用途 |
|---|---|
| `criteria.md` | 跑前寫定的三組與預期；跑後追加的結果、偏離與判準沒涵蓋的觀察 |
| `task-prompt.md` | 排程任務的提示原文 |
| `check_notifications.py`、`open_item.py` | 兩支工具（服務在 127.0.0.1:18765；開單每次等 45 秒） |
| `stop_hook.py` | `UserPromptSubmit` hook：是這個排程任務、而且工作目錄有 `STOP` 時擋下 |
| `runs/20261011T1610Z/` | 逐輪紀錄 `task-runs.json`、服務端 `requests.jsonl`、開單 `items.json`、hook 呼叫 `hook.log`、hook 設定與核准後被存下的設定 |

## 自己重跑

1. 啟動服務：`python ../lab-schedule/service.py 18765 <資料夾> new --today`。資料夾**不要**放在任務的工作目錄裡，否則 Claude 讀得到開單紀錄。
2. 在 Claude Desktop 的 Code 分頁 → Routines → New routine → Local，貼上 `task-prompt.md`，選好工作資料夾與模型，權限模式選「自動」。
3. 要試煞車：把 `stop_hook.py` 設成**任務工作資料夾**的 `.claude/settings.json` 裡的 `UserPromptSubmit` hook，再在工具目錄放一個 `STOP` 檔。
4. 跑完記得停用並刪除任務。

## 界線

各組一次，只示範現象；每輪花費 Desktop 未回傳；人工介入 4 次。結果見 `criteria.md`。
