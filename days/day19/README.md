# Day 19｜讓 Claude 專心判斷，把固定檢查交給程式

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10420353) |
| 今天練習 | 跑一次十二案固定檢查，再讓 Claude 對誘餌來源產出結果，看入口是退回、待查還是交人核對 |
| 需要什麼 | Python 3；模型試跑另需 Claude Code CLI |
| 跑什麼 | `cd days/day19/lab-result-gate; python run_cases.py` |
| 看什麼 | 12 案是否全部符合預期（八退回、三交人核對、一待查）；誘餌案 Claude 有沒有拿別筆通知的接收紀錄充數 |
| 範本 | 無 |
| 原件 | days/day19/lab-result-gate（check_result.py、run_gate.py、fixtures/、runs/model-*） |
| 界線 | 固定資料與小樣本；39 次全對只支持這批案例，不是準確率；程式通過不等於建議可執行 |


[回 30 天索引](../../README.md)
