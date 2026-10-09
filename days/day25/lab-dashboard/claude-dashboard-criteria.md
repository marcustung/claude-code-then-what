# Day 25 Claude 用 gcx 建 Grafana Dashboard：事前判準（2026-10-09，跑前寫定，跑後不改）

## 設計

逐筆對帳由 `build.py` 完成，`publish_to_grafana.py` 把結果送進 Day 24 的本機 LGTM（每 30 秒重送一次）：

- 指標：`work_expected`、`work_matched`、`work_unmatched`、`work_status`（狀態在 `status` 標籤）、`sender_reported_sent`（發送端自報的送出數，不是接收端證據）。
- Log（service_name=`day25-work-view`）：未對上的事件，帶 run、state、order_id、request_id、notification_id；資料不足的輪次標 `unknown_identity`。
- 五輪：`sep-missing`（9 月重放，9 筆對上 3 筆）、`sep-fixed`（9／9）、`sep-slow`（資料不足）、`d24-normal`、`d24-slow`（Day 24 兩輪，9／9）。

Claude 拿到通知契約，以及「資料在 Grafana、服務名稱 day25-work-view」；指標與欄位要它自己用 gcx 探索。工具：gcx 的查詢、資源與 Dashboard 子命令（Editor 帳號，只在本機教學 Grafana），`create-dashboard` Skill 以 `--plugin-dir` 載入。不給本檔、`build.py` 的結果、`grafana-publish-rows.json` 或 Day 25 文章。本機 Grafana 沒有 Image Renderer，`gcx dashboards snapshot` 預期失敗，Claude 須以查詢驗證面板。

## 自動檢查（`check_dashboard.py`，讀它建好的 Dashboard，逐一執行面板查詢）

| # | 檢查 | 通過條件 |
|---|---|---|
| D1 | Dashboard 存在 | UID `day25-work-view` 可取得，至少 3 個面板 |
| D2 | 完成率用接收端證據 | 有面板查詢對 `sep-missing` 算出約 0.333（3／9） |
| D3 | 不拿發送端自報數當完成 | 沒有任何面板查詢以 `sender_reported_sent` 當完成數或完成率的分子 |
| D4 | 未知看得見 | 有面板查詢使用 `work_status` 或 Loki 的 state，能讓 `sep-slow` 顯示資料不足 |
| D5 | 事件清單 | 有 Loki 面板查詢 `day25-work-view`，結果含 notification_id |

## 人工檢查（看畫面與面板設定）

| # | 檢查 |
|---|---|
| H1 | 一眼看得出「今天先查哪一批」（`sep-missing`） |
| H2 | `sep-slow` 沒有被呈現成「完成率 4.6%、247 筆遺失」這種確定結論 |
| H3 | 重放資料與 Day 24 資料有區分（data_source 或標題說明） |

## 結果分類

- **成立**：D1–D5 全過，且 H1–H3 全過。
- **方向對、仍需人補**：D1、D2、D3 過，其餘有缺。
- **有價值的失敗**：D3 不過（用發送端自報數算完成，等於重演 Day 23 的「監控說成功」），或 H2 不過。

另記：工具呼叫次數、被權限擋下的指令、snapshot 是否嘗試、費用與耗時。sonnet，一次；人工時間未量。
