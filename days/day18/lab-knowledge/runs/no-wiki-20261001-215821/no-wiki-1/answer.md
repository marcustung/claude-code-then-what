**結論:現在不能判定需不需要補送,也不建議補送。** 只證明了送出端宣稱成功,還沒證明使用者或接收端有收到。

**說明**:`wiki/INDEX.md` 不存在,工作目錄只有 `sources/`。以下改以 `ticket.json`、`sender-event.json`、`sources/Program.cs`、`Cancellation.cs`、`design-review.md` 核對,沒有套用任何 wiki 知識。

**已確認**
- 事件 `notify_sent`(`demo-order-18`/`demo-notify-18`,`sync:true`)是合成 fixture,不是實際日誌(`sender-event.json:2`)。
- `notify_sent` 只在 sink 回 2xx 後才寫(`Program.cs:217,222`、`257-260`)。它代表送出端收到成功回應,不代表使用者收到。
- 只有真正從未取消變成已取消時才建通知(`Program.cs:79`、`Cancellation.cs:25`)。已出貨(409)和重複取消都不通知(`Program.cs:74-76`)。
- `sync:true` 只出現在同步路徑 `SendOnce`(`Program.cs:222`),而該路徑只在 `faults.SyncNotify` 時啟用(`Program.cs:85-86`)。所以這是演練用的同步注入,不是預設行為。
- 報告版本與提供的程式碼版本相同(`ticket.json:6-7`)。

**尚缺**
- 接收端日誌、部署設定證明、補送契約、具名 Owner(`ticket.json:10`)。
- 真實的 `logs.jsonl`,包括 `cancel` 的 `transitioned` 值和 `request_id`。fixture 缺少 `request_id`、`run_id`、`ts`、`version`,與程式碼實際寫出的欄位不符(`Program.cs:222`、`159`)。
- 實際的 `OC_SINK_URL` 和 `OC_FAULTS`。`/version` 寫死回報 `async`(`Program.cs:37`),不能用來證明目前模式。
- `design-review.md:7` 說明本輪未跑 .NET,所以行為只是讀程式碼的推論。

**下一步查哪裡、用什麼條件**
1. 查 `OC_RUN_DIR/logs.jsonl`,時間窗 `2026-10-01T00:00–00:05Z`,條件 `notification_id=demo-notify-18`。確認 `cancel` 的 `transitioned=true`,且沒有 `notify_dead_letter`。
2. 查接收端日誌,用同一個 `notification_id`。
   - 有紀錄:不用補送,改查接收端到使用者之間的環節。
   - 無紀錄但送出端是 2xx:查 sink 位址是否設錯,或接收端是否不是真的接收。
3. 查 `startup` 日誌的 `faults_loaded` 和 `sink`,確認部署設定。

**是否可補送**
目前不行。程式沒有補送入口,補送契約也沒提供。沒有契約就不知道接收端會不會去重,貿然重送可能造成使用者收到重複通知。只有在接收端確認沒收到、而且契約允許重送時才可考慮。

**需要誰決定**
票上沒有具名 Owner(`ticket.json:10`),我不編造人選。這個決定要由補送契約的 Owner 下,應先指派人選。