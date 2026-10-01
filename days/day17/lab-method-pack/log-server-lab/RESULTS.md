# Day 17 Log server 實跑對照

## 資料來源

本次 run 為 live-20261001-02；沿用 delivery-hardening-local-r2，先核對發布包 manifest，重新啟動 API，產生三筆建立與取消請求。ingestion-checks.json 六項均符合预期。不是歷史 Log 回放，沒有改原始發布包。

## 修正過程

1. setup-failure-complete：Skill 載入失敗，MCP 傳輸設定不相容，未取得 Log，不能算成成功查核。
2. model/complete、missing-receipts、query-failure：修正載入與連線後實際查到資料；遇到小數秒格式問題。完整案沒有独立以 notification_id 查接收端，所以不判成整套流程通過。前兩案曾在結果整理時遇到字串 message，從原始 trace 恢復答案與工具紀錄，不冒充另一次模型執行。
3. revision-r2.json：時間窗改成事先確認的整秒 UTC，明確載入 plugin Skill，開放必要唯讀標籤工具，Skill v0.1.1 要求獨立接收端查詢與固定 sender_status。
4. model/r2/：同一組已蒐集 Log，以三個新 session 重跑。各案成功載入 Skill，查詢範圍與任務一致，工作目錄雜湊未變。

## 最終結果

| 情境 | sender_status | receiver_status | Log 查詢數 | 回合 | 此輪模型費用 USD |
|---|---|---|---:|---:|---:|
| complete | confirmed | confirmed | 2 | 12 | 0.1050014 |
| missing-receipts | confirmed | unknown | 3 | 13 | 0.1218990 |
| query-failure | unknown | unknown | 2 | 11 | 0.0931096 |

費用僅為修正後三次，總計 0.32001；不含前面的失敗與第一輪，不是整個實驗成本。

missing-receipts 第一次使用 service 標籤而非 service_name，得到零筆；讀取標籤後修正，找到 API 紀錄，再以 notification_id 查接收端仍零筆。此過程支持「先核對查詢，再解釋零筆」。query-failure 的實際 502 與成功查詢的空結果有分開。

verify-results.py 檢查 36/36 通過，見 runs/live-20261001-02/verification-r2.json。另人工核對三份 answer 與 tool-results：完整案只確認接收，不推到退款完成；缺件案保留未知；故障案保留 502、未擅換來源。這些是本次有限情境，不是完整語義評測、權限不足測試或團隊效益。

## 原件入口

- acceptance-plan.json：模型實跑前定的情境預期。
- runs/live-20261001-02/package-manifest.json、audit/：版本及真實請求、接收端對照。
- 同 run 的 workspaces/：修訂後模型輸入；原始任務另保存在 audit/*-task-before.json。
- 同 run 的 model/r2/*/trace.jsonl：完整工具軌跡。
- provenance.json 保留 prepare 階段狀態；completion.json 記錄後續完成狀態，兩者依時間解讀。

公開匯出可能遮蔽本機絕對路徑，使 input-manifest 與公開副本不再相符。歷史雜湊核對結論對應原工作區；讀者應用新 run 自己產生 manifest，不可用公開副本字節重算來冒充原環境驗證。
