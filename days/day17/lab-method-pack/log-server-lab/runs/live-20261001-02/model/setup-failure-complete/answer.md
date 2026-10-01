# 查核結果：Log 查詢無法執行，接收端狀態 unknown

## 1. 工具狀態
- **Skill**：`trace-notification` 沒出現在 Skill 工具清單，呼叫回 `Unknown skill`。我改讀 `.claude/skills/trace-notification/SKILL.md` 並照它的迴圈做，這不是正式載入。
- **Grafana MCP**：`mcp.json` 有設定 `grafana`，只啟用 `datasource,loki`、`--disable-write`、`--max-loki-log-limit 30`。但這個工作階段沒有任何 Grafana/Loki 工具，我只有 Glob、Grep、Read、Skill。
- 我沒有改用其他資料來源，也沒有執行 shell。
- **下一步**：請在此工作階段啟用 `grafana` MCP（可能需要重啟並核准）。啟用後我再照下列條件查。

## 2. 任務範圍（來源：`task.json`）
- 訂單 `live-20261001-02-complete`，版本 `delivery-hardening-local-r2`，本機 Docker 教學環境
- 時間窗 `2026-09-30T19:26:22.525875Z` ～ `19:26:23.768514Z`（UTC）
- datasource_uid `day17-loki`，標籤 `lab_case="complete"`
- 服務 `order-api`、`notification-receiver`

## 3. 程式與設計核對（已完成）
- `src/Program.cs:49-94`：取消成功轉態（`transitioned`）時才建通知。`notification_id` 是新產生的 GUID，寫入 `cancel` 日誌和回應。
  - 預設非同步：第 88 行寫入 Channel，由 NotificationWorker（第 225 行起）POST 到 sink。
  - 失敗重試 3 次（200/400/800 ms），之後記 `notify_dead_letter`。
  - 成功時記 `notify_sent`（第 260 行）。
  - `OC_FAULTS` 設了 `sync_notify` 時走 `SendOnce`（第 86 行）。
- `notify_sent` 只代表 sink 回了 2xx，不等於接收端已核對。`notification-receiver` 的程式不在本工作區，所以只能靠 Log 核對接收端。
- `design/design-review.md` 第 1 點說 Worker 送達與 HTTP 回應沒有固定先後，所以不能用時間順序推論。第 7 點說 .NET 本輪未跑。
- 我沒有在 workspace 找到 `VERSION` 檔。`task.json` 的 `delivery-hardening-local-r2` 是否等於實際部署版本，要靠 Log 的 `version` 欄位確認。

## 4. 預定的最小查詢（尚未執行）
1. 列出 `day17-loki` 的資料源，確認該 uid 存在。
2. 用 `{lab_case="complete"}` 加上 `order-api`，在時間窗內搜尋 `order_id` 的 `cancel` 事件，取得 `notification_id`、`transitioned`、`result`。
3. 用該 `notification_id` 查 `order-api` 的 `notify_sent`、`notify_deferred`、`notify_dead_letter`。
4. 用同一個 `notification_id` 查 `notification-receiver`，對照 `refund_requested`、`attempt` 與收據。

## 5. 結論與 JSON
我沒有查到任何 Log，也沒有證據說通知沒送到；接收端和發送端都是 unknown。

```json
{
  "order_id": "live-20261001-02-complete",
  "sender_status": "unknown",
  "receiver_status": "unknown",
  "missing_sources": [
    "Grafana MCP 工具（datasource、loki）未在本工作階段提供，day17-loki 尚未查詢",
    "order-api 的 cancel／notify_* 日誌",
    "notification-receiver 的接收日誌",
    "notification-receiver 的原始碼不在工作區"
  ],
  "next_action": "啟用 grafana MCP 後，依上列第 1-4 項查詢，先以 order_id 找 notification_id，再核對接收端；未取得接收端日誌前不得判定已送達或未送達，也不補送、不結案。"
}
```