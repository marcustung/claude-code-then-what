**版本**：task 要求與提供的來源版本都是 `delivery-hardening-local-r2`，一致。以下依 `design-review.md` 的七點核對 `Program.cs` 與 `Cancellation.cs`。

| # | 原說法 | 來源定位 | 結論 | 理由與範圍 |
|---|---|---|---|---|
| 1 | 通知頁：read/decide/write 非整體原子，個別 lock 不保證並行取消安全 | `Program.cs:105-113` | **修訂** | `TryCancel` 在同一個 `_g` lock 內完成讀取、`Cancellation.Cancel` 與寫回，所以單筆取消的狀態轉移是原子的。通知入列在 lock 之外（79-88），所以不是整個請求原子。範圍是單程序記憶體；多實例沒有來源。 |
| 2 | 順序：Domain:69、建通知:79、入列:84、日誌:88、回應:89 | `Program.cs:64,79-93` | **修訂（行號）／保留（順序）** | 行號已漂移。現況是 64 `TryCancel`、82 建通知、88 入列、92 日誌、93 回應。預設分支入列在回應前。`sync_notify` 注入時改為同步送出（85-86）。Worker 送達與回應沒有固定先後（`:227`）。 |
| 3 | FakeSink 沒存 refund_requested，不等於 payload 沒變 | `:246` | **保留（部分）** | payload 確實帶 `refund_requested`。FakeSink 的程式不在 sources，其行為未知。 |
| 4 | API 仍有 Shipped 判斷，退款計算在 Domain | `:74`、`Cancellation.cs:19` | **保留** | 409 的判斷在 API，`refundRequested` 在 Domain。 |
| 5 | 檔案日誌不等於記憶體佇列，持久性限制針對訂單與佇列 | `:37,160,18` | **保留** | 訂單在記憶體，佇列是 `Channel`，日誌是 `AppendAllText`。重啟後日誌是否留存，來源沒說，所以不下結論。 |
| 6 | 決策表有沿用項 | 無決策表 | **未知** | sources 沒有決策表。程式只註記 NC-02、NC-03、NC-05、BR-02、BR-04，無法判斷哪些是沿用、哪些是提案。 |
| 7 | 本輪未跑 .NET，測試是待執行設計 | — | **保留** | 我也沒有執行，只讀了程式。 |

**程式有、wiki 缺的事實**
- 只有狀態真的轉移時才通知（`:79`）。出貨拒絕與冪等都不通知。
- Worker 失敗後重試 3 次（200／400／800ms），仍失敗進 dead_letter。
- 壓力延後最多 5 次，`sent` 只在 ack 後才加。

**設計理由**：`OC_TEST_DELAY_MS` 的註解說它是「放大既有 race window」，但 `:71` 在 lock 之後，來源沒有說明它放大的是哪個 race。這點我不補造。

**`notification.md` 修訂草稿**
```
# 取消與通知（核對版本：delivery-hardening-local-r2）
- 單筆取消的 read/decide/write 在 OrderStore 同一 lock 內完成（Program.cs:105-113）；
  通知入列在 lock 外，整個請求並非原子。範圍：單程序記憶體。
- 僅 transitioned 時建通知並入列（預設在回應前；sync_notify 注入時同步送）。
  Worker 送達與 HTTP 回應無固定先後。
- 失敗重試 3 次，仍失敗進 dead_letter；延後最多 5 次，sent 只在 ack 後加。
- 未知／待驗：FakeSink 行為、決策表沿用項、多實例並行、測試結果（未執行）。
來源：design-review.md、Program.cs、Cancellation.cs
```