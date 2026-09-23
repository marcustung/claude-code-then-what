逐箭頭核對結果：

1. `C->>A: POST /orders/id/cancel`(48行) 一致。
2. `A->>S: TryGet(id)` / `S-->>A: before`(63行) 一致，但圖漏畫 actor 為空時的 401 分支(57–62行)。
3. `A->>D: Cancel(before)`(69行) 一致。
4. `A->>D: Transitioned(before, result)`(70行) 一致。
5. **順序不一致：程式有分支，圖只畫了單一路徑。** 圖預設 `Transitioned` 回傳 true 直接進入通知與 200 回應，但程式在70行取得 `transitioned` 後，於72–74行有三種結果：`before.Shipped` → 409 不通知；`transitioned` → 200 且 `store.Put`；否則 idempotent → 200 不通知。圖完全省略了 `before.Shipped`（409, rejected_shipped）與 idempotent（200, 不通知）這兩條分支，只畫出「transitioned=true」這條路。
6. `A->>S: Put(id, result.Order)`(73行) 一致，但圖畫在 `A-->>C: 200 ...` 之前，程式碼上 `store.Put` 確實在73行、回應在89行之前執行，順序方向正確。
7. `A-->>C: 200 {...}`：圖畫在 enqueue 通知**之前**，但程式碼中通知邏輯(76–85行)其實在回應(89行)之前就先執行完畢（包含 `await channel.Writer.WriteAsync(n)`），**回應是最後才送出的**。這是圖錯：應為先 enqueue 通知，client 才收到 200，而非圖上「先回200再enqueue」。
8. `A->>N: enqueue Notification`：程式碼是 `channel.Writer.WriteAsync(n)`(84行)，只在 `faults.SyncNotify` 為 false 時走此路徑；若為 true 則改為 `NotificationWorker.SendOnce`(82行) 同步呼叫。圖只畫了非同步 enqueue 這條，缺少 `SyncNotify` 為 true 時的同步分支，屬程式有分支而圖未畫出（非圖錯，是簡化/遺漏）。
9. `N->>K: POST /notify` / `K-->>N: 200`：屬 NotificationWorker 內部行為，Program.cs 48–92行看不到實作，無法核對；但依上一點,若為 SyncNotify 分支，其實是 `A` 直接同步呼叫 `SendOnce`，並非由獨立的 N 非同步觸發，圖上仍只呈現非同步版本。

## 結論摘要
- **圖錯（順序顛倒）**：第7點，回應200應在通知 enqueue **之後**才送出（Program.cs 76–89行），圖畫反了。
- **程式有分支、圖未呈現**：
  - actor 為空 → 401（57–62行）
  - before.Shipped → 409 不通知（72行）
  - idempotent（未 transition）→ 200 不通知（74行）
  - faults.SyncNotify 為 true 時是同步呼叫 `NotificationWorker.SendOnce`，而非透過 channel 非同步 enqueue（81–84行）

其餘箭頭（TryGet、Cancel、Transitioned、Put）順序與程式一致。