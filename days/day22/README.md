# Day 22｜Claude 查完了，團隊知道下一步嗎？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10421518) |
| 今天練習 | 三步：①不給分派規則讓 Claude 排今天的工作 ②加 --hook 掛 Stop hook，讓「還缺證據不能交給服務 Owner」每次都被檢查 ③用 Mod 看板看每件事做到第幾步、交給誰、hook 擋過什麼 |
| 需要什麼 | Claude Code CLI（Mod 需 v2.1.287 以上）、Python 3 |
| 跑什麼 | `cd days/day22/lab-view; python run-triage.py 1; python run-triage.py 1 --hook; claude --plugin-dir mod 後輸入 /work-view（不想花錢可直接看 demo/）` |
| 看什麼 | 負責人（程式裡叫服務 Owner）被塞了幾件；hook 擋了什麼、Claude 怎麼改；看板上有沒有「證據齊了卻交給查核者」的那件（hook 沒管這個方向） |
| 範本 | 無 |
| 原件 | days/day22/lab-view（run-triage.py、hook/check_worklist.py 與 settings.example.json、mod/ 看板、demo/、三組各 3 次的工作清單與軌跡、FINDINGS.md） |
| 界線 | 31 筆教學資料、每組 3 次，不估穩定度比例；規則只放在 hook，看板只讀結果；「缺證據交查核者」是本例的團隊約定 |


[回 30 天索引](../../README.md)
