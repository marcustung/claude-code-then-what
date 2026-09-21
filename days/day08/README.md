# Day 8｜我替 AI 出了考卷，結果錯的是我的答案

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10415265) |
| 今天練習 | 對一份你自己出的考卷做反向核對：讓 Claude 追呼叫鏈、每個結論附檔案:行號，再用 check_citations.py 抽驗 |
| 需要什麼 | Claude Code CLI；Python 3 |
| 跑什麼 | `cd days/day08/lab; powershell -NoProfile -File run.ps1 r4; python check_citations.py r4` |
| 看什麼 | 每筆引用三項都過嗎；結論跟 answer-key-v1.md 哪一格相反；再跑 guess-1 看抽驗怎麼把猜的行號全部擋掉 |
| 範本 | [grading-table.md](../../templates/grading-table.md) |
| 原件 | days/day08/lab（教學示範 repo、prompt、runs r1–r3、負對照 notools／guess 各兩次、抽驗程式） |
| 界線 | 教學示範 repo 七檔未編譯；真實更正紀錄不公開 |


[回 30 天索引](../../README.md)
