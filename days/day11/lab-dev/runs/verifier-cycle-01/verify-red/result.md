## 執行的指令與結果

1. `dotnet run --project tests/DomainTests`
   輸出：SC-01 ~ SC-07 全部 `PASS`，結尾 `PASS: 全部條件通過`（純 Domain 層，對照 `specs/rules-v2.md` BR-01~BR-04）。

2. `python verify-integration.py verifier-red`
   輸出：`{"run": "verifier-red", "checks": 11, "pass": false}`，exit code 1。
   來源：`runs/verifier-red/report.json` 中 `"build": true`（建置成功，非環境/建置失敗），11 項檢查裡 10 項 PASS，僅 `notification-ids-and-flags` 為 `false`。

結論：這不是環境或建置失敗，是真實的行為不一致，屬於「已重現的缺陷」。

## plan.md 是否達成

- 步驟 1、2（Domain 對規格 SC-01~07）：**達成**，`dotnet run` 全 PASS。
- 步驟 3「檢查 HTTP 回應、log、送往測試接收端的 payload」：**未達成**。三者彼此不一致，見下。

## 不一致的來源（帶行號）

以 `request_id: verifier-red-5`（第一次取消 `paid` 訂單，`paid=true, shipped=false`）為例：

| 來源 | 欄位 | 值 | 出處 |
|---|---|---|---|
| HTTP 回應 | `refund_requested` | `true` | `runs/verifier-red/requests.json` 第78行 |
| logs.jsonl | `refund_requested` | `true` | `runs/verifier-red/logs.jsonl` 第2行 |
| 送到測試接收端的 payload | `refund_requested` | **`false`** | `runs/verifier-red/payloads.json` 第8行 |

HTTP 回應與 log 都正確反映 Domain 判定的 `RefundRequested=true`（符合 BR-03），但實際 POST 給接收端的通知卻是 `false`。

程式碼位置：`src/Api/Program.cs` 第79行

```csharp
var n = new Notification(Guid.NewGuid().ToString("N"), id, rid, runId, "order_cancelled", false);
```

這裡建立 `Notification` 時把 `RefundRequested` **寫死為 `false`**，沒有使用同一行上下文已算出的 `result.RefundRequested`（第69行 `var result = Cancellation.Cancel(before);`，第88~89行回應與 log 都正確取用了 `result.RefundRequested`，唯獨第79行漏接）。所以 Domain 層本身是對的（測試全過），但 API 層在組裝通知物件時的欄位傳遞出現遺漏，導致下游通知系統會收到錯誤旗標（若真的接了退款服務，會造成該退款的訂單沒被標記要退款）。

`unpaid` 訂單（`verifier-red-7`）三處皆為 `false`，剛好與寫死值一致，所以掩蓋了問題，只有「已付款」案例才會曝露出這個落差。

## `notification-ids-and-flags` 檢查未涵蓋的欄位

檢查邏輯（`verify-integration.py` 第57行）：

```python
check('notification-ids-and-flags', sorted((x.get('order_id'), x.get('refund_requested')) for x in payload) == [('paid',True),('unpaid',False)], payload)
```

此檢查只比對 `(order_id, refund_requested)` 這一個 tuple，**不檢查**：

- `notification_id`：是否唯一、格式是否符合、是否與該次取消一一對應（此次雖是真的 GUID 沒重複，但檢查本身不驗證唯一性或格式）。
- `request_id`：是否與觸發它的 HTTP 請求 `request_id` 相符（本次剛好對得上，但不是被斷言的）。
- `run_id`：是否與本次執行的 run 一致。
- `kind`：值固定為 `"order_cancelled"`，未驗證是否會因情境（例如 v2 之後若有其他 kind）而變化。
- `attempt`：目前恆為 `0`（因為這次沒有觸發 `SyncNotify`／重試／`notify_deferred`／`dead_letter` 分支），此檢查完全沒有涉及重試次數或延後（deferral）情境下的欄位正確性。
- `shipped` 訂單、`unauthorized`（401，`verifier-red-9`）等不應產生通知的情境，未驗證「確實沒有送出通知」這件事本身有沒有被覆蓋到其他檢查裡（本次是靠 `payload` 只有兩筆 tuple 間接反映，不是直接斷言 count）。

## 未測試/超出本次範圍（依 `report.json.limits` 與 `plan.md` 第6點）

- `limits` 欄位明載：僅本機、順序請求、有界觀察；未涵蓋並發、真實付款/授權、重啟復原、遠端部署。
- 本次執行 `faults_loaded: false`（`logs.jsonl` 第1行），代表 `SyncNotify`、`DropOverQueue`（notify_deferred/dead_letter 路徑）等故障注入分支**這次沒有被行使**，所以 `NotificationWorker` 重試/延後/死信邏輯（`Program.cs` 第210~253行）目前的正確性未經此次驗證檢驗。
- `verify-integration.py` 對 `paid-log-first-and-repeat` 只檢查第一次 (`true`) 與重複取消 (`false`) 兩筆的 `refund_requested`，未涵蓋 `shipped`/`unauthorized`/`not_found` 情境下 log 的完整欄位正確性。

## 小結

- Domain 規則（`src/Domain/Cancellation.cs`）符合 `specs/rules-v2.md` v2，七個驗收場景皆通過（有 `dotnet run` 輸出為證）。
- 整合層破口明確可定位：`src/Api/Program.cs:79` 建立通知時把 `RefundRequested` 寫死 `false`，未使用同一次請求已算出的 `result.RefundRequested`，造成「回應/日誌」與「實際送出的通知 payload」不一致，違反 `plan.md` 第3點要求。
- `verify-integration.py` 的 `notification-ids-and-flags` 檢查範圍窄，只斷言 `order_id`+`refund_requested` 的組合，其餘欄位（`notification_id`、`request_id`、`run_id`、`kind`、`attempt`）與故障注入路徑（延後/重試/死信）均未在本次執行中被驗證，屬於「未讀到不等於不存在」但目前確定「未被此次檢查覆蓋」的範圍。

本報告僅陳述觀察與程式碼位置，未修改任何原始碼、測試、規格或執行器。