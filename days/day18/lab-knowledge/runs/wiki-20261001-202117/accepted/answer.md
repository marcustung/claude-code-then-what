**結論（版本 delivery-hardening-local-r2）：** `notification.md` 大致可保留，另有三處建議補充。我只讀檔，沒有執行程式。`sources` 內沒有 VERSION 檔，版本是否為 r2 只能靠 task.json 與 INDEX 的宣告，無法從程式驗證。

**逐項核對**

1. 「TryCancel 在同一 lock 內取得、取消、寫回」
   - 來源：Program.cs:105-114，Cancellation.cs:8-22。
   - 判定：**保留**。
   - 理由：程式與說法一致。
   - 範圍：同程序、同一 OrderStore，不含通知。

2. 「通知建立與入列在 TryCancel 之後，非同一交易」
   - 來源：Program.cs:64、79-88。
   - 判定：**保留**。
   - 理由：兩者都在 lock 之外。
   - 範圍：不能推到跨程序或 exactly-once。

3. 「舊說法：個別 lock 不保證並行取消安全」（design-review 第 4 點）
   - 判定：**修訂（已修）**。
   - 理由：r2 的讀、判斷、寫在同一 lock 內。`transitioned` 由 before 與 result 推出，重複取消只有一次為 true。這是我讀程式的推論，沒有並行實測。
   - 範圍：僅限 lock 內三步。

4. 「notify_sent 只由 worker 寫入」
   - 來源：Program.cs:85-86、222、257-260。
   - 判定：**修訂（已修）**。
   - 理由：sync_notify 時由 SendOnce 寫入，並帶 `sync=true`。
   - 範圍：僅限故障注入設定。

5. 「notify_sent 只證明發送端見到成功，沒驗退款」
   - 來源：Program.cs:217、248。
   - 判定：**保留**。
   - 理由：成功判斷只看 `IsSuccessStatusCode`，payload 只帶 `refund_requested` 旗標。
   - 範圍：「接收端 confirmed」依賴的 sink 不在 sources，無法核對。

6. 「訂單與 Channel 在記憶體」
   - 來源：Program.cs:15、18、37。
   - 判定：**保留**。
   - 理由：程式與說法一致。
   - 範圍：log 檔不在此限。

7. design-review 第 1 點的行號（69、79、84、88、89）
   - 判定：**修訂**。
   - 理由：與現行 Program.cs 對不上，現在是 64、82、88、92、93。「入列在回應前」仍成立。
   - 範圍：引用時改用方法或事件名稱，不用行號。

8. 「本輪未跑 .NET」（design-review 第 7 點）
   - 判定：**保留為歷史界線**。
   - 理由：本次我也沒執行，所以只能說「未實測」，不能說「已驗證」。

**未知，不補寫：** SLA、正式接收端、補送授權、值班 Owner；sink 如何保存收據；r2 與程式註解中 v1.1.0 / v1.2.0 的對應關係。

**notification.md 修訂草稿（只加有來源的內容）**

> 新增「失敗與分支」：
> - worker 與 SendOnce 都是首次加 3 次重試（間隔 200／400／800 ms，共 4 次）。全失敗寫 `notify_dead_letter`（Program.cs:203、223、262-266）。
> - sync_notify 下，SendOnce 失敗不會丟例外，請求仍可回 200。通知結果要看 log，不能看 HTTP 狀態（Program.cs:85-93）。
> - `notify_enqueued_total` 在 sync 路徑也會累加（Program.cs:84），不等於「進入 Channel」。
> - `/version` 的 `notification_mode` 固定為 "async"，不反映 sync_notify（Program.cs:37），不能用它判斷模式。
> - 已出貨回 409、重複取消回 200，這兩種都不通知（Program.cs:74-79）。
> - notify_drop_over_queue 會把通知重排最多 5 次，超限後改走一般送出（Program.cs:230-240）。僅限演練注入。

**待確認：** 若要宣稱「此程式就是 r2」，需提供 VERSION 或版本對照。