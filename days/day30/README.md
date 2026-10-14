# Day 30｜工具買完後，我們終於能怎麼回答總經理？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10424336) |
| 今天練習 | 打開 Claude Code 的 OTel 遙測重跑 Day 28 兩組（A1 重疊、C1 沒權限），看遙測比退出碼多看到什麼、仍看不到什麼；再填五層結帳表，未知寫未知 |
| 需要什麼 | Python 3、Claude Code CLI（約 US$0.06） |
| 跑什麼 | `cd days/day30/lab-otel; python otlp_receiver.py otel 4318（另開視窗）；設定 OTEL 環境變數後 python run.py A1 C1（完整指令見 README）` |
| 看什麼 | otel/logs.jsonl 的 tool_decision（C1 是 reject，退出碼卻是 0）與 tool_result（A1 兩輪都 success），再對照 runs/*/A1/items.json 的 4 張重複單 |
| 範本 | [five-layers-ledger.md](../../templates/five-layers-ledger.md) |
| 原件 | days/day30/lab-otel（criteria.md、otlp_receiver.py、run.py、runs/20261012T030354Z；身分欄位已遮）；公司數字只在文中以比例與趨勢出現，不附原始資料 |
| 界線 | 各組一次，示範遙測內容；遙測事件帶使用者 email、帳號與組織 ID，收進共用平台前要先定存取與保存規則；工具秒數不是人工節省 |


[回 30 天索引](../../README.md)
