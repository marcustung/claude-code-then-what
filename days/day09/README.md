# Day 9｜需求寫好了，Claude 就能開工嗎？

| 格 | 內容 |
|---|---|
| 文章 | [文章](https://ithelp.ithome.com.tw/articles/10415774) |
| 今天練習 | 拿一條真的要改的規則，給 Claude 三種材料各跑一次唯讀分析：只給程式、加呼叫端、給完整規格，看它各問得出什麼 |
| 需要什麼 | Python 3；另跑模型需 Claude Code |
| 跑什麼 | `cd days/day09/lab-scope; python verify.py` |
| 看什麼 | verify.py 只做機械檢查（來源雜湊、工具是否限唯讀、八組布林旗標等價），不檢查語意；再讀 runs/ 下各次 result.md，找它把「材料沒給」寫成「不存在」的那幾句 |
| 範本 | [change-scope-card.md](../../templates/change-scope-card.md) |
| 原件 | days/day09/lab-scope（三組唯讀實跑、規格與程式快照、八組布林核對）；days/day09/lab-intake（訪談實跑與 grilling plugin、無 skill 對照） |
| 界線 | 靜態分析不是 .NET 功能測試；三組提示不同，不是控制實驗；訪談只驗第一輪提問，沒有真人回答；讀者重跑不保證相同答案 |


[回 30 天索引](../../README.md)
