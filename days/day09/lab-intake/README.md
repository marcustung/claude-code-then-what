# Day9：PM spec 到 RD 開工前訪談

這是新的不完整 spec 教學演示，不是既有 rules-v2 的真人澄清過程。真人答案0筆，不代表已核准開發。

## 已做

1. 固定 upstream grilling skill commit，保持原文，LICENSE與provenance.json保存。
2. 本機 plugin 載入，Claude Sonnet medium 單輪只讀。trace 確有 Skill 呼叫，四項問題與原始回答保留。沒有 Agent 工具，模型自行讀檔，不聲稱完整重現上游委派流程。
3. CodeGraph1.6.0 CLI 在 graph-project 副本索引。npm安裝與CLI分開；不是Claude MCP呼叫。query找到符號，callers/impact漏列API已知呼叫，files清單則包含API。
4. 以原始碼搜尋交叉核對。沒有隔離缺邊根因，不推論普遍語言品質。

## 閱讀與重跑

先讀 spec.md、runs/interview-01/result.md、audit.md、runs/codegraph-01/ 的原始輸出。

`python verify.py`：不呼叫模型，檢查輸入雜湊、實際Skill呼叫，以及圖查詢與已知原碼呼叫的差異。它不裁決語意正確。

`python run.py my-new-run`：在此資料夾執行，需已登入Claude Code，會消耗用量；新目錄才可執行。保存原始trace/meta，不覆寫既有答案。這是非互動第一輪，沒有自動編造使用者回答。

互動探索：`claude --plugin-dir ./interview-plugin --permission-mode plan`，呼叫 `/intake-interview:grilling` 並提供spec及程式範圍。這是可操作入口，沒有宣稱本文已跑完整互動訪談。

圖譜重跑：在本資料夾 `npm ci --prefix codegraph-tool --ignore-scripts --no-audit --no-fund`，使用 package-lock 固定相依。以 `node codegraph-tool/node_modules/@colbymchenry/codegraph/npm-shim.js` 為CLI前綴，再接 runs/codegraph-01/commands.json 內的 init/query/callers/impact 參數；把其中絕對路徑換成自己的 graph-project。新結果另存，不覆蓋已保存輸出。

本機安裝依 npm 包的 bin 宣告使用 npm-shim.js；首次按 GitHub source 猜 dist/bin/codegraph.js 得 MODULE_NOT_FOUND，改正入口後索引成功。那不是語意查詢失敗。沒有做全域 install/MCP註冊。

## 邊界

草案刻意列出三類未決問題，因此不能把模型提出它們當成盲測發現率。它的增量在於附上程式位置與具體選項，但過度建議仍需裁決。没有正式接受、工程省時或團隊採用證據。套件僅本機備稿；trace 對外分享前需去識別與敏感資訊檢查。
