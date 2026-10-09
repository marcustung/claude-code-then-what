我沒辦法執行這支驗證腳本，因為系統要求核准，我就不再重試。所以問題 1 和 2 的改造資料驗證還沒做。下面的結果只來自對 data/ 三輪的重跑，不含驗證。

## 重跑結果（已輸出到 `out/`）

| run | 判定 | 說明 |
|---|---|---|
| missing-notification-…193704 | investigate | 應完成 9 筆，只有 3 筆收據。這輪已結束，佇列深度為 0，另外 6 筆是被靜默丟失。 |
| missing-notification-…193835 | matched | 9 筆都有收據，而且 `notification_id` 和發送端記錄一致。 |
| slow-sync-control-…191636 | **investigate**（原本是 waiting） | 應完成 259 筆，只有 12 筆收據。這輪已結束，卻還有 253 筆留在佇列裡沒送出。 |

## 「完成」的新定義

一則通知要同時符合三項，才算完成：

1. 有一筆成功轉換（HTTP 2xx 且 `transitioned=true`）。
2. 接收端有收據，而且 `run_id`、`request_id`、`order_id` 都對得上。
3. 收據的 `notification_id` 等於發送端 log 為這個 request 記下的 `notification_id`（NC-06）。

之前只比對了前兩項，也就是筆數和 `request_id`。

## 三個問題的修法

1. **`notification_id` 不同**：現在這筆會標成 `mismatch`，整輪判 investigate，而且不計入已確認數。
2. **發送端完全沒有 `notification_id`**：以前缺少的值被當成 `None`，檢查就被跳過了。現在沒有發送端 id 的收據標成 `unverified`，整輪判 unknown，原因寫「先補發送端紀錄」。這種情況不會被判成 matched。
3. **15 天前的快照判 waiting**：waiting 只在這輪還在進行時才成立。manifest 是 `terminal` 或有 `ended` 就表示不會再有新收據。這時如果佇列深度還大於 0，代表通知卡住，判 investigate，原因寫明結束時還有 253 筆沒送出。

## 還需要你確認

- 如果快照已結束，而且缺少佇列深度，現在仍判 unknown，沒有改成 investigate。
- `mismatch` 和 `unverified` 是新增的 state，HTML 的事件表也加了對應顏色。
- 我沒有改 `data/` 和 `notification-contract.md`。契約目前仍是 `proposed`，修法依它的 NC-04 和 NC-06 寫成，如果之後修改，要再對照一次。

如果你核准，我可以再跑那支驗證腳本。它在 scratchpad 的 `t.py`，會用 193835 的副本做出 `mismatch` 和 `nosender` 兩份改造資料。