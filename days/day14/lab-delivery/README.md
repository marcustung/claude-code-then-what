# 訂單服務交付與接手實驗

Day 14–17 的本機教學延伸。承接 `../sdlc-development`；歷史程式、負載數字及原件不改標成同一版本。

## 前提與邊界

Python 3、.NET 9 SDK/runtime、k6 1.3.0。Day 14 真實診斷另需已登入的 Claude Code CLI（本次 CLI 支援 --safe-mode）。不自動安裝依賴。不執行正式部署、真實退款或對外通知；本機 API 與假接收端只綁 loopback。

baseline 是並行缺口演示，fixed 是單程序原子取消修正；release-next 在 fixed 上新增 /version。記憶體儲存、未實作正式認證、未做跨程序一致性及持久化通知。X-Actor 僅教學檢查，不是安全的登入機制。

## 從這個目錄重跑

每次使用新名稱，不覆蓋既有 runs。以下失敗演練第一行預期 exit 1。

```sh
python deliver.py baseline my-failure --with-concurrency --diagnose-with-claude
python deliver.py fixed my-candidate --with-concurrency
python load-candidate.py my-load --candidate my-candidate --k6 k6
python analyze-load.py my-load
python deliver.py release-next my-next --with-concurrency
python rehearse-release.py my-rollback --old my-candidate --new my-next
python prepare-handoff.py my-rollback --elapsed-seconds 0 --output my-wait
python prepare-handoff.py my-rollback --elapsed-seconds 300 --output my-escalate
```

第一行的診斷參數會傳送 baseline 的 Program.cs、Cancellation.cs 與限定檢查摘要至 Claude 服務；需先確認自己有權傳送，會產生模型費用。去掉參數可完全不呼叫模型。腳本不讀任意終端輸出或環境變數進提示；診斷使用空工具表與 safe mode，失敗狀態始終保留。safe mode 不是作業系統沙箱。

k6 不在 PATH 時，將 --k6 後面的值換成完整執行檔路徑。load-candidate.py 驗證包雜湊後直接啟動 Api.dll，不重編譯；收集 k6 樣本、.5 秒 metrics、日誌與假接收端收據。通知觀察最多二十秒，不能證明觀察窗外永不重複。

rehearse-release.py 依預設演練停止／啟動程序，在新版階段注入接收端503，再回復舊包及接收端200。沒有負載平衡或零停機保證；每次停止都會失去記憶體訂單。prepare-handoff.py 只模擬時限與產生事件，不發送訊息、不補送通知。

## 已保存的證據

| 範圍 | 原件 |
|---|---|
| 自動失敗診斷 | runs/acceptance-auto-01、acceptance-auto-01-concurrency |
| r1 候選包 | runs/candidate-checked |
| 本文壓測 | runs/acceptance-load-02（01 為無階段標籤的前輪） |
| r2 候選包 | runs/acceptance-next-01 |
| 更新與回復 | runs/acceptance-rollback-01 |
| 等待與升級 | runs/acceptance-handoff-wait、acceptance-handoff-escalate |

並行修正及 trace-success/trace-failure 仍保留為補充。Claude 真實執行只有記錄中具體列出的呼叫；不把提示範本當成實跑。Azure DevOps 遠端接入、公開 repo 匯出與真人值班不在這些本機結果中。
