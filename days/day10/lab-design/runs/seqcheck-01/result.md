## 逐箭頭核對結果

1. **C→A POST** 對應 `Program.cs:48` ✅ 一致
2. **A→S: TryGet(id)** 對應 `Program.cs:63` ✅ 一致（但圖省略了 `id` 不存在時回 404 的分支，`Program.cs:63-67`）
3. **A→D: Cancel(before)** 對應 `Program.cs:69` / `Cancellation.cs:8-22` ✅ 一致
4. **A→D: Transitioned(before, result)** 對應 `Program.cs:70` / `Cancellation.cs:25` ✅ 一致
5. **A→S: Put(id, result.Order)** 對應 `Program.cs:73` ✅ 順序一致，但圖未畫出前提條件 `!before.Shipped`（`Program.cs:72`）——已出貨時不會 Put，屬圖的簡化省略，非矛盾
6. **A-->>C: 200 {...}** 與 **A→N: enqueue Notification** 順序**不一致**：
   - 程式實際順序是先 enqueue 通知（`Program.cs:76-84`），再組 log、才 `return Results.Json`（`Program.cs:86-89`）
   - 圖中卻畫成先回應 Client、後才 enqueue，**這是圖錯**，應對調這兩個箭頭順序
7. **N→K: POST /notify** 與 **K-->>N: 200**：屬於 `NotificationWorker`（在此片段外的背景消費者，走 `channel.Writer.WriteAsync`，`Program.cs:84`），與 Client 回應本就解耦、非同步發生，圖上畫在 `A-->>C` 之後是合理的（無矛盾）。

## 結論
圖中唯一與程式順序不一致之處：**"A-->>C: 200" 應該在 "A→N: enqueue Notification" 之後**，而不是之前。原因是圖錯，程式碼在 `Program.cs:76-89` 明確地先 enqueue 通知再回傳 HTTP 回應。其餘箭頭順序與程式一致，僅有 401/404 分支及 `Shipped` 判斷條件未畫出（圖的合理簡化）。