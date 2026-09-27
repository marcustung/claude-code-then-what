# Day 14｜Claude 寫好了，怎麼交成一個能跑的版本？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10418159) |
| 今天練習 | 用 baseline 跑一次交付入口讓並行檢查失敗，看流程自動把限定摘要交給 Claude 診斷；再用 fixed 跑一次，四步通過才產生候選包 |
| 需要什麼 | Python 3；.NET 9 SDK；最後一步要呼叫模型需 Claude Code CLI 並已登入（會產生費用） |
| 跑什麼 | `cd days/day14/lab-delivery; python deliver.py baseline my-failure --with-concurrency --diagnose-with-claude` |
| 看什麼 | runs/my-failure/report.json 的 steps 應為 ci=0、concurrency=1，passed:false，且 diagnosis.delivery_stays_failed 為 true（診斷成功不會把失敗蓋成通過）。再開 diagnosis-result.json 看它把事實與推論分開寫、並自己標「尚未驗證」。想看通過路徑：python deliver.py fixed my-candidate --with-concurrency，四步全 0 才有 package 與雜湊清單 |
| 範本 | 無 |
| 原件 | days/day14/lab-delivery：deliver.py、diagnose_failure.py、verify.py、baseline／fixed 兩版取消流程、runs/acceptance-auto-01（自動呼叫的輸入與回覆）、runs/candidate-checked（四步通過的候選包） |
| 界線 | 本機實跑，無遠端 CI 或正式發布；本輪沒有讓 Claude 改碼，只做唯讀分析；推論「無人為延遲仍會重現」未驗證；Owner 發布接受未取得 |


[回 30 天索引](../../README.md)
