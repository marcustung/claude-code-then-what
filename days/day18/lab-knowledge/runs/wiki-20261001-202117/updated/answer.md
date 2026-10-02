**範圍**：task.json 要求與提供版本皆為 delivery-hardening-local-r2。sources 內沒有 VERSION 檔，所以只能靠標示確認版本。我只讀檔，沒有執行程式。

**逐項核對**

| # | 原說法 | 來源定位 | 判定 | 理由與範圍 |
|---|---|---|---|---|
| 1 | TryCancel 在同一 lock 內讀、判斷、寫 | Program.cs:105-114 | 保留 | 僅限同程序、同一 store instance。 |
| 2 | 通知建立與入列在 lock 外 | Program.cs:79-88 | 保留 | 不是持久化交易，也不是跨程序 exactly-once。 |
| 3 | 正常路徑為非同步，sync_notify 走 SendOnce | Program.cs:85-88、208 | 保留並補充 | 另有 notify_delay_ms 和 notify_drop_over_queue 注入（Program.cs:187-188、230）。後者的延後會重排到隊尾，所以不保證順序。 |
| 4 | notify_sent 由 worker 在 HTTP 成功後寫入 | Program.cs:247-260 | 修訂 | sync_notify 時由請求路徑的 SendOnce 寫入，帶 sync=true（:222）。另有重試與 dead_letter 沒寫進 Wiki。 |
| 5 | confirmed 需接收端同 notification_id 的紀錄 | sources 無接收端 | 未知 | sources 沒有接收端程式。此為定義，無法由 sources 核對。 |
| 6 | 沒驗退款完成 | Program.cs:215 | 保留 | 程式只傳 refund_requested 旗標。 |
| 7 | 訂單與 Channel 在記憶體 | Program.cs:15、18、102 | 保留 | 檔案日誌不等於記憶體，不能說重啟必然消失。 |
| 8 | 舊設計「個別 lock 不保證並行取消安全」 | design-review.md 第 4 點 | 修訂（changes.md 已處理） | 它描述的是舊狀態，r2 已被 TryCancel 取代。 |
| 9 | 「本輪未跑 .NET」 | design-review.md 第 7 點 | 限定範圍 | 只指當時查核，不代表本次未執行。 |
| 10 | design-review 第 1 點的行號（69/79/84/88/89） | design-review.md 第 1 點 | 修訂 | 行號與現行 Program.cs 不符。現行入列在 :88，回應在 :93。 |

**Wiki 尚未記載、程式可見的行為**
- 已出貨（409）與重複取消（idempotent）不通知，見 Program.cs:74-79。
- 只有 `Transitioned` 為真才建立通知，見 Cancellation.cs:25。
- 同程序內並行取消，依程式推論最多一次轉換、一則通知。這是推論，沒有測試。
- 失敗最多送 4 次（200/400/800ms 退避），之後進 dead_letter。
- 重送使用同一個 notification_id。接收端若已處理但回應遺失，可能收到重複通知。這是由程式推導，沒有實測。
- 缺 X-Actor 回 401。這是實作行為，沒有設計理由的來源。

**未知，不補造**
- 公司 SLA、正式接收端、補送授權、值班 Owner。
- NC-02、NC-03、BR-xx 規格文件不在 sources，程式註解只能當指標。
- r2 與註解中 v1.1.0、v1.2.0 的對應關係。
- 通知順序與回應先後的業務要求。

**notification.md 修訂草稿**

```
## 可核對的實作（補充）
- notify_sent：非同步路徑由 worker 寫入；sync_notify 由請求路徑 SendOnce 寫入（sync=true）。皆只代表發送端見到 HTTP 成功。
- 失敗最多送 4 次（200/400/800ms），之後記 notify_dead_letter。重送沿用同一 notification_id；接收端是否去重沒有來源，未知。
- 只有狀態真正轉換才通知；已出貨（409）與重複取消不通知（Program.cs:74-79，Cancellation.cs:25）。規格 NC-02/NC-03 不在 sources，僅依程式說明。
- 演練注入還有 notify_delay_ms、notify_drop_over_queue；後者的延後會重排到隊尾，不保證順序。
- 同程序並行取消最多產生一則通知，這是程式推論，未測試。

## 未取得
sources 無 VERSION 檔與接收端程式；r2 與程式註解版本號（v1.1.0／v1.2.0）的對應未知。
```

另外建議在 changes.md 註明 design-review 第 1 點的行號已過時。