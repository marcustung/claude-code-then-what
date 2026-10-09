建置成功（0 警告、0 錯誤），但只有編譯通過。我沒有跑執行期或負載測試。

## 真正的改動（`src/Api/Program.cs`）

**根因：** 取消處理器在 `await CustomerHistory.FetchAsync()` 之前先讀了訂單（`before`）。16 個併發請求都讀到「未取消」的舊快照。500ms 後每個請求都用這份舊快照判斷，所以 16 個都算出 `transitioned=true`。每個也都 `Put` 並排入通知，結果就是 16 筆不同的 `notification_id`。

**修法：**
1. 在 `OrderStore` 新增 `TryCancel`，在同一把鎖內完成讀取、`Cancellation.Cancel`、`Transitioned` 判斷和寫入。鎖內沒有 `await`。
2. 處理器仍先 `await FetchAsync()`，也就是 500ms 查詢完成後才呼叫 `TryCancel`。因此用的是查詢後的最新狀態，而不是舊快照。
3. 同一訂單只有第一個拿到鎖的請求會 `transitioned=true` 並排入通知。其餘請求走 `idempotent`，回 200、`transitioned=false`、不通知。
4. 回應和 `409` 判斷改用鎖內取得的 `current`，不再用舊的 `before`。

**沒有動的部分：**
- 500ms 延遲還在，沒有縮短。
- 沒有調整 ThreadPool，也沒有用 `Task.Run`。
- 授權（401）、404、已出貨 409、`refund_requested`、`RequestAudit` 的呼叫與通知內容格式都維持原樣。
- `Cancellation.cs`、測試和規格都沒改。

## 代價
- 每次取消多一次短暫的鎖，只包字典操作，和既有的 `OrderStore` 鎖同一把，爭用很小。
- 開頭的 404 檢查還是在 await 之前，之後才會有第二次讀取。因為服務不刪單，所以 `TryCancel` 直接用 `_d[id]`。若將來加入刪單功能，要改成處理找不到的情況。

## 尚未驗證或需決策
- **還沒重跑 16 併發同單測試。** 預期是 1 次 `transitioned=true`、15 次 `false`、接收端只有 1 筆通知，但這是依程式邏輯推論，不是實測結果。
- 384 張不同訂單的負載測試也沒重跑。
- 這次修的是競態。`RequestAudit` 無界成長和 `JsonlLog` 同步寫檔這兩個隱患沒處理，需要你決定是否另開議題。
- 通知接收端是否收齊且不重複，需要用接收端自己的紀錄對照。

這次對話的結論（競態根因加上鎖內重新讀取、判斷、寫入的做法）值得存起來，可以用 `/brain-save` 存入大腦。