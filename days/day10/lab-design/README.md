# Day 10 設計分析包

教學規格對固定快照的唯讀分析，不是已完成實作。

- `manifest.json`：輸入來源與 SHA256。
- `reader-prompt.txt`：原始實跑提示。
- `runs/design-01/`：原始結果與工具紀錄，保留錯誤。
- `verification-notes.md`：核對與採用界線。

執行 `python verify.py` 核對來源與唯讀工具紀錄。
另跑需安裝並登入 Claude Code，會消耗模型用量：`python run.py my-design-01 reader`。不可覆蓋既有 run 名稱。

沒有專案檔與完整相依環境，這是閱讀分析包，不能以此宣稱已完成 .NET 編譯或整合測試。


先在本目錄執行指令。每次換新的 run 名稱，避免覆蓋既有紀錄。新回覆位於 runs/<name>/result.md，trace.jsonl 是工具事件，meta.json 是執行參數與狀態，stderr.txt 留錯誤。verify.py 只核對 manifest 與 design-01，不代表所有設計推論正確。

唯讀模型只回傳文字。讀者從 result.md 另存 Mermaid 到 diagram-to-check.md，將核對提示存成 check-my-diagram.txt，再以新的 claude -p 呼叫核對；接受的決定由讀者整理成 plan.md。
