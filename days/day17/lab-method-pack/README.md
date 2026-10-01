# Day17 查核方法包實驗

目標：讓查核方法在沒有原對話時重用，並在缺件時保留未知。

## 結構
- package/.claude/skills/trace-notification/SKILL.md：方法、輸入、判準、輸出格式。
- package/.claude/skills/trace-notification/scripts/collect.py：依訂單与通知ID整理事件，區分缺失、空集合與格式錯誤。
- cases/complete：既有 r2 健康情境的教學資料，不含文章或判讀答案。
- cases/missing-receipts：相同輸入，但不提供接收端紀錄。
- source-map.json：原件對照。原始紀錄未修改。
- local-checks.json：本機腳本驗證結果。

## 使用
將 package 的 .claude 目錄複製至自己的測試專案，依案例格式準備 task.json、data、src 與 design。
先在專案根目錄執行 `python .claude/skills/trace-notification/scripts/collect.py .`，再於 Claude Code 使用 `/trace-notification`。
此腳本只支援本包JSON格式，接其他Log平台需適配。它是確定性的紀錄整理，不是根因判斷器。

## 實驗邊界
本機腳本七項檢查與三次離線模型對照已完成，見 runs/。新增 [Log server 實跑](log-server-lab/README.md)與[結果](log-server-lab/RESULTS.md)：修訂版 Skill 經 MCP 查核三種情境，36 項檢查通過。
這是同一電腦的教學素材測試，不是團隊採用，也沒有人工減載結論。腳本由執行端先跑，模型只讀結果，不宣稱模型自己執行腳本。

## 工具優先修訂
目前 package/Skill 改成使用既有 Log 與程式工具，collect.py 為可選離線入口。cases/ 內初版 Skill 保留，未重跑模型。核心驗收為方法載入、查詢範圍、同事件關聯、缺件與查詢失敗；local-checks.json 只驗整理器。
