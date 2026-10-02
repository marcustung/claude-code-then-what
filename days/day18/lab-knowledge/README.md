# Day18 系統知識的查核與修訂

先執行 `python verify.py` 核對來源與連結。安裝並登入 Claude Code 後，在本目錄執行 `python run-wiki.py`，會呼叫 Claude 服務並消耗額度，每次最多 2 美元、300 秒。工具只提供 Read/Grep/Glob，無 MCP、無寫入，模型需遵守工作目錄範圍；工具允許清單不是作業系統檔案隔離。

四次各自新 session：舊說法、整理後 Wiki、未提供的 r3、接受同步分支修訂後。每次保存提示、工具軌跡、回答、費用與輸入雜湊。fixtures/wiki-before 固定改前知識，wiki/ 是接受修訂後知識；前三次使用同樣 r2 程式。r3 是缺來源測試，不是實際版本。

## 已完成紀錄

runs/wiki-20261001-202117/review.json：四次成功、輸入未改，均讀 INDEX 與 Program.cs。舊說法也能被原始碼更正；新 Wiki 漏了同步通知分支，Claude 指出後由作者核對寫回，再開新 session 確認讀到。模型另指出缺 VERSION 檔。來源身分由作者的 source-manifest.json 對照，不能寫成模型驗證了部署版本。

sources/ 原件完全保留。模型只拿兩個程式檔與舊設計；歷史 Claude 回答不放進工作目錄，避免答案洩漏。原件清單中的設定與歷史回答供作者稽核。工作區刻意不提供接收端與規格，不能由這次實跑驗證送達或設計意圖。

## 讀者重做後要看什麼

1. tool-calls.json 是否真的讀了索引、相關頁面及來源。
2. answer.md 的鎖範圍是否限定在同程序同一 store，沒有擴稱通知持久化。
3. unknown-version 是否拒絕將 r2 套用到 r3。
4. accepted 是否保留同步分支修訂；新發現仍需回到來源核對。

每種情境只有一次，不估準確率或省時。review.json 的語意判定是作者檢閱；執行／讀檔／雜湊檢查不能代替語意評估。

## 下一個任務：是否需要補送

執行 `python run-next-task.py`。它會用 Claude 額度跑兩個新 session；工單與發送事件都是明標 SYNTHETIC 的教學資料，不會查 live Log 或補送。固定同樣程式、工單、事件與提示，對照有無 applicability.md。輸入快照固定在 fixtures/wiki-before-next-task 與 fixtures/wiki-next-task-accepted，新增結果各存新目錄。

紀錄：runs/next-task-20261001-203725/review.json。兩輪都找到同步路徑且保留送達未知；前輪自行建議補送沿用 ID，人工核對後未接受；後輪要求補送方法、去重與授權，未替它決定 ID。單次差異不能當成穩定增益，提示本身已限制不可補造授權。缺 config.alloy，所以查詢標籤仍需下一步驗證。

原始程式取用差異：before 以 Read 讀 Program.cs；after 以 Grep content 查 Program.cs 的相關事件與方法，未整份重讀。引用取消規則也使用既有知識頁，不能據此稱為全程式驗證。
