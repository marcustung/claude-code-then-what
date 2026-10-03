# Day 20｜我能跑，別人拿到也能跑嗎？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10420719) |
| 今天練習 | 把查核工具組放進一個全新目錄，先跑自測，再請 Claude 用 Skill 查核；接著拿掉啟動授權再跑一次，看停在哪裡 |
| 需要什麼 | Python 3；Claude Code CLI 並已登入（會產生費用） |
| 跑什麼 | `cd days/day20/lab-handoff; python run-handoff.py complete; python run-handoff.py marketplace` |
| 看什麼 | runs/ 下兩次的 summary.json：outer_gate 的 state（READY_FOR_REVIEW 或 NEEDS_FOLLOWUP）與 permission_denials；第二次沒有啟動授權時，腳本是否被擋 |
| 範本 | 無 |
| 原件 | days/day20/lab-handoff：package（查核工具組 v2.1.2、INSTALL.md、settings.template.json）、cases、runs（十次實跑的指令、軌跡、操作者重跑的檢查）、findings/README.md（含五種權限寫法） |
| 界線 | 同一台作者機的隔離設定，不是另一台機器或真人同事；每情境一次；只靠 Skill 或專案設定的權限為何沒生效尚未查清 |


[回 30 天索引](../../README.md)
