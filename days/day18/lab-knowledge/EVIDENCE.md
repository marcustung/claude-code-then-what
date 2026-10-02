# Day 18 實跑紀錄與重跑方式

本文比較的是教學輸入下的模型回答，不是線上補送結果。原始輸入與回答均保留，不覆寫歷史紀錄。

## 如何重跑

取得 `examples/day18-knowledge-lab` 後，安裝並登入 Claude Code，在該目錄執行：

```text
python verify.py
python run-next-task.py
```

第一行核對來源雜湊與連結；第二行呼叫 Claude，每輪最多 2 美元、300 秒，並建立兩個新對話。這是實驗設定上限，不是實際費用。請比較 `answer.md` 的操作建議，再以 `tool-calls.json` 核對來源取得過程。

## 原始比較：before

**結論：目前不建議補送。** 發送端只證明「發送端看到成功」，接收端有沒有收到仍是 unknown。

**已確認**
- `demo-notify-18` 有 `notify_sent`，且 `sync:true`（sender-event.json）。該事件是合成資料，不是實際擷取的 log（同檔 `fixture`）。
- `sync:true` 只由 `SendOnce` 寫入，這條路徑只在 `sync_notify` 開啟時走（Program.cs:85-86、222）。事件本身不能證明部署上確實開著這個設定。
- 寫入條件是 HTTP 回應成功（Program.cs:217、222；wiki/notification.md）。它不代表接收端已確認，也不代表退款完成。
- 取消在同一 lock 內完成（Program.cs:105-113）。通知建立在 lock 之外（Program.cs:79-88），不是同一筆交易。
- 訂單與 Channel 都在記憶體中（Program.cs:18、102）。

**尚缺**
- 接收端紀錄：ticket.json 的 `available` 寫明未提供。
- 部署設定證明：確認 `OC_FAULTS` 的 `sync_notify` 和 `OC_SINK_URL`。ticket.json 只有版本字串。
- 補送契約和具名 Owner：未提供（ticket.json；notification.md「未取得的決策」）。
- `sources/config.alloy` 不在工作目錄。log-query.md 引用了它，所以標籤和收集設定我無法核對。
- 沒有該筆 `cancel` 的 log，所以不知道 `request_id` 與 `transitioned`。

**下一步查哪裡、用什麼條件**（依 log-query.md，需有 Loki 存取權才能做）
1. 查接收端：`service_name="notification-receiver"`，時間窗 2026-10-01T00:00:00Z 到 00:05:00Z，內容比對 `notification_id=demo-notify-18`。
   - 零筆時，先核對標籤、服務與時間窗，再分辨是工具錯誤還是真的沒有紀錄。
   - 有紀錄才能說接收端已收到。
2. 查發送端：`service_name="order-api"`，`order_id=demo-order-18`，確認 `cancel` 事件 `transitioned=true`，並確認沒有 `notify_dead_letter`。
3. 取得部署的設定證明，確認 `sync_notify` 與 sink 位址。

**能否補送**
- 接收端無紀錄、設定也確認後，才可能需要補送。
- 補送時要沿用同一個 `notification_id`，但接收端是否去重沒有來源可證，因此不能保證不重複通知。
- 補送契約沒有提供，所以現在不能補寫，也沒有人授權補送。

**需要誰決定**
- 補送要不要做、怎麼做：由具名服務 Owner 決定，但目前沒有指定人選。
- 接收端與部署設定的證明：由接收端與部署的負責人提供，具體是誰也未提供。

## 原始比較：after

**結論：目前不能判定是否需要補送，也不能授權補送。** 只有發送端證據，沒有接收端證據。

**已確認**
- 發送端事件 `notify_sent` 存在，`sync: true`，order_id 為 demo-order-18，notification_id 為 demo-notify-18（sender-event.json）。該檔是合成資料，不是實際擷取的 log。
- `sync=true` 代表走 sync_notify 的 `SendOnce` 路徑，由請求路徑同步送出。`Program.cs:86、222` 可核對。正常的 worker 路徑不帶 sync（`Program.cs:259-260`）。
- `notify_sent` 只在 `resp.IsSuccessStatusCode` 為真時寫入（`Program.cs:217、222`）。因此它只證明發送端看到 HTTP 成功，不證明使用者收到、接收端處理完成或退款完成（wiki/notification.md；wiki/applicability.md 第 7 列）。
- ticket 的版本與提供的程式版本都是 delivery-hardening-local-r2，一致（ticket.json）。
- 重複取消不是補送入口。已取消時不會再建立通知（wiki/applicability.md 第 9 列，來源 Cancellation.cs 與 Program.cs 的 Transitioned 分支）。

**尚缺**
- 接收端 log，或相同 notification_id 的接收與處理紀錄（ticket.json 的 available 欄）。
- 部署中 sync_notify 設定的證明。程式只說明有這個分支，ticket 的環境標示不是部署證明。
- 補送契約：補送方法、接收端去重規則、授權。
- 具名的 Owner。
- 公司 SLA 與正式接收端也沒有提供（wiki/notification.md「未取得的決策」）。

**下一步查哪裡、用什麼條件**
1. 到接收端 log 查。依 wiki/log-query.md，service_name 用 `notification-receiver`，發送端是 `order-api`。
2. 條件：notification_id = demo-notify-18，order_id = demo-order-18，時間窗 2026-10-01T00:00:00Z/00:05:00Z。這兩個 ID 要從 log JSON 內容比對，不是標籤。
3. 零筆結果先核對標籤、服務與時間窗，並區分工具錯誤與成功的空結果。查不到只能記為 unknown，不等於沒送達（wiki/log-query.md）。
4. 同時向服務維護者確認當次部署的 sync_notify 設定來源。

**能否補送**
- 目前不可以。沒有補送 API、去重契約或授權，補送可能造成重複通知（wiki/applicability.md「缺件與決策」）。
- 只有在查得接收端沒有紀錄，且補送契約與授權都到位後，才能再評估。

**需要誰決定**（wiki 的建議分工，不是公司已採用的規範，也沒有具名人選）
- 服務維護者：確認查詢來源與部署版本。
- 有權接受重複副作用風險的人：決定補送條件。
- 這兩個角色都要由團隊指定，我不編人名。

**限制：** 我只讀了檔案，沒有執行任何指令，也沒有呼叫外部系統。wiki 是教學用資料，不是正式服務手冊。


## 補跑 next-task-20261001-205729 / before

**結論：目前不建議補送。** 補送的前提是接收端沒收到，這點還沒確認。

**已確認**
- 這是合成教學工單，只有發送端事件。`demo-notify-18` 的 `notify_sent` 帶 `sync:true`（sender-event.json）。
- 程式版本與回報版本相同，都是 delivery-hardening-local-r2（ticket.json）。
- `sync:true` 代表走 `sync_notify` 同步分支：`SendOnce` 在請求路徑上送出，收到 `IsSuccessStatusCode` 才寫 `notify_sent`（Program.cs:85-86、217、222）。
- 通知只在 `transitioned` 為真時建立（Program.cs:79-83），所以這筆是真的完成了取消。
- 這個事件只證明發送端看到 HTTP 成功。接收端是否 confirmed，另需相同 `notification_id` 的接收紀錄，也沒驗退款（wiki/notification.md:15）。
- 失敗路徑會寫 `notify_dead_letter`（Program.cs:223）。目前沒有證據顯示這筆走到那裡。
- 程式裡沒有補送 API 或補送契約，我只 grep 到發送與重試，沒有補送入口。

**尚缺**
- 接收端紀錄：ticket.json 的 `available` 欄位寫明沒提供。
- 部署設定證明：目前無法確認實際是否開了 `sync_notify`，以及 `OC_SINK_URL` 指向哪裡。只能說事件形狀符合同步分支。
- 補送契約，以及具名 Owner。
- 事件本身是「shaped after」的合成資料，不是真實擷取的 log（sender-event.json）。
- 訂單與 Channel 都在記憶體，程序重啟後的狀態無法推定（notification.md:17）。

**下一步查哪裡、用什麼條件**（依 wiki/log-query.md，需有可用的 log 查詢權限；目前 mcp.json 的 `mcpServers` 是空的，本次沒有可用工具）
1. 接收端：`service_name="notification-receiver"`，時間窗 `2026-10-01T00:00:00Z/00:05:00Z`，用 JSON 內容比對 `notification_id=demo-notify-18`。
2. 發送端：`service_name="order-api"`，同一時間窗，找 `demo-order-18` 的 `cancel` 事件、同一個 `notification_id`，以及是否有 `notify_attempt_failed` 或 `notify_dead_letter`。
3. 先核對標籤與時間窗，再判讀零筆結果。工具錯誤和成功的空結果要分開記。
4. 部署設定要向有權限的人索取，不從 wiki 猜。

**能否補送**
- 接收端若有同 ID 紀錄，就不用補送，問題轉向使用者端或通知內容。
- 接收端若確定沒有，才有補送理由。但目前沒有補送契約，也沒有授權與冪等保證。重送時 `notification_id` 是否沿用、接收端是否去重，都沒有來源可證。所以現在不能直接補送。
- 只查到「沒有紀錄」時只能記為 unknown，不能判定未送達（log-query.md:12）。

**需要誰決定**
- 服務 Owner：確認補送行為、接受條件與授權。ticket 沒有指定具名人選，需要工單方指派（notification.md:19-21）。
- 接收端維護者：確認去重與重送是否安全。來源沒有提到這個角色，是我的建議。

## 補跑 next-task-20261001-205729 / after

**結論：目前不能判定要補送，也不能說已送達。現有證據只到發送端。**

**已確認**
- 事件 `demo-order-18` / `demo-notify-18` 有 `notify_sent`，且 `sync:true`（sender-event.json）。這個事件是 SYNTHETIC fixture，不是實際擷取的 log。
- `sync:true` 只會由 `SendOnce` 寫入（Program.cs:222）。這表示該路徑是同步送出，當次 `sync_notify` 應已啟用，但程式碼不能證明部署上有開（Program.cs:86、190）。
- 成功條件是發送端收到 HTTP 成功（`IsSuccessStatusCode`，Program.cs:217、248）。所以 `notify_sent` 只代表發送端看到成功，不代表接收端處理完成或使用者收到（wiki/notification.md；applicability.md 第 1 列）。
- 重複取消不能當補送入口：已取消時 `Transitioned` 為 false，不會再建通知（Program.cs:72，Cancellation.cs；applicability.md 第 3 列）。
- 版本一致：回報與提供的程式都是 `delivery-hardening-local-r2`（ticket.json）。這只是工單自述，不是部署證明。

**尚缺**
- 接收端 log，也就是相同 `notification_id` 的接收與處理紀錄（ticket.json「available」）。
- 部署設定證明，包括 `sync_notify` 當次是否開啟、`OC_SINK_URL` 指向哪裡。
- 補送契約：補送 API、接收端去重規則。
- 具名的 Owner。
- 公司 SLA、正式接收端、補送授權，來源都沒有（notification.md「未取得的決策」）。
- `config.alloy`：log-query.md 引用它，但工作目錄沒有這個檔案。收集設定因此無法核對。

**下一步**
1. 以 `service_name=notification-receiver`（log-query.md）、時間窗 `2026-10-01T00:00:00Z/00:05:00Z`、`notification_id=demo-notify-18` 查接收紀錄。`notification_id` 要從 log JSON 內容串接，不是固定標籤。
2. 查詢前先核對 datasource 與標籤。零筆時，先分清是工具錯誤還是成功的空結果，再核對標籤、服務與時間窗。
3. 查不到時只能記為 unknown，不等於沒送達（log-query.md、applicability.md）。
4. 向服務維護者確認部署版本、`sync_notify` 設定來源與查詢來源。

**是否可以補送**
- 現在不可以。沒有接收端證據，也沒有補送契約與授權。
- 若接收端確認沒收到，仍需先確認補送方法與去重，再由有權接受重複通知風險的人決定。
- 呼叫取消 API 重送不可行。

**需要誰決定**
- 服務維護者：確認部署版本與查詢來源。
- 有權接受重複副作用風險的角色：決定補送。
- 兩者都沒有具名，需由團隊指定。這是建議分工，不是已採用的規範（applicability.md）。

## 補跑 next-task-20261001-205813 / before

**結論：目前不能判定是否需要補送，也不建議先補送。**

**已確認**
- 發送端有 `notify_sent`，`sync=true`，ID 為 demo-notify-18（sender-event.json）。這筆是合成資料，並非實際擷取的 Log。
- `sync=true` 只會出現在 `sync_notify` 的同步分支（Program.cs:85-86、222）。這是演練用的故障注入設定，正常是非同步。
- `notify_sent` 只代表發送端收到 HTTP 成功回應（Program.cs:217、257-260），不代表接收端已收到（wiki/notification.md）。
- 通知是在 `TryCancel` 的 lock 之外才建立與送出（Program.cs:79-88）。
- 訂單與 Channel 都在記憶體中（Program.cs:18、102）。

**尚缺**
- 接收端中 notification_id 相同的紀錄（ticket.json：未提供接收端 Log）。
- 部署設定證明。`sync_notify` 是否真的啟用、`OC_SINK_URL` 指向哪裡，都未確認（ticket.json）。
- 補送契約、SLA、授權、具名 Owner（ticket.json、notification.md）。
- `sources/config.alloy` 不在工作目錄，log-query.md 的標籤說明無法核對原始設定。
- 缺 task.json，datasource 也沒有提供（INDEX.md）。

**下一步查哪裡、用什麼條件**
1. 查接收端 Loki：`service_name="notification-receiver"`，時間窗 2026-10-01T00:00:00Z 到 00:05Z，JSON 內容比對 `notification_id=demo-notify-18`，再比對 `order_id=demo-order-18`（log-query.md）。
2. 查發送端 `service_name="order-api"`，看同一 ID 有沒有 `notify_attempt_failed`、`notify_dead_letter`，或重複的 `notify_sent`（Program.cs:219、223）。
3. 判讀：
   - 找到接收紀錄，才算 confirmed，不需補送。
   - 查無結果時，先核對標籤與時間窗，並分清是工具錯誤還是空結果。核對後仍沒有，也只能記為 unknown，不能寫成未送達。

**能否補送**
- 目前不可。Program.cs 沒有補送機制，接收端是否以 notification_id 去重也未知，隨意重送可能造成重複通知。
- 條件：接收端確認未收到，並且 Owner 核准補送方式。

**需要誰決定**
- 需要服務 Owner 決定，但工單沒有指名，我不補寫人選。補送授權與 SLA 也要由業務或 Owner 確認（notification.md「未取得的決策」）。

## 補跑 next-task-20261001-205813 / after

**結論：目前不能判定要補送，也不能判定已送達。** 這張工單缺少接收端證據。

**已確認**
- 發送端事件 `notify_sent`，order_id=demo-order-18、notification_id=demo-notify-18，帶 `sync:true`。來源：sender-event.json。
- 這個事件只代表發送端收到 HTTP 成功。程式在 `resp.IsSuccessStatusCode` 為真時才寫入，SendOnce 在 Program.cs:217、222，worker 在 248、259–260。它不代表接收端處理完成，也不代表使用者收到。來源：wiki/notification.md、applicability.md。
- `sync:true` 對應 `faults.SyncNotify` 分支，通知由請求路徑的 `SendOnce` 同步送出（Program.cs:85–86、222）。但設定是否真的開啟，現有資料無法證明。
- 通知只在 `transitioned` 為真時建立（Program.cs:79–83）。重複取消走 idempotent 分支，不會建通知（Program.cs:76），所以重送取消不能當補送入口。來源：applicability.md 第 3 列。
- 版本一致：ticket 回報與提供的程式都是 delivery-hardening-local-r2。來源：ticket.json。
- 訂單與 Channel 都在記憶體，程序重啟後不能假設資料還在。來源：notification.md。

**尚缺**
- 接收端 log、部署設定證明、補送契約、具名 Owner。來源：ticket.json 的 `available`。
- 本次 `sync_notify` 的實際設定來源。
- 「API 回 200」只是請求紀錄的說法，沒有對應的 cancel 事件可核對。ticket 與 sender-event 都只是合成資料（SYNTHETIC），不是實際擷取的 log。

**下一步查哪裡、用什麼條件**
1. 查接收端 log：`service_name=notification-receiver`，用 notification_id=`demo-notify-18` 串接，時間窗 2026-10-01T00:00:00Z 至 00:05:00Z。來源：log-query.md、ticket.json。
2. 同時查發送端 `service_name=order-api` 的 `cancel` 事件，用 order_id 關聯，確認 transitioned=true 與 notification_id 一致。
3. 零筆結果時，先核對標籤、服務名稱和時間窗，並分清是工具錯誤還是成功但為空。來源：log-query.md。
4. 查當次的部署與設定來源，確認 `sync_notify`。datasource 由 task.json 提供，目前工作目錄沒有這個檔案，所以未知。

**能否補送**
- 目前不可以。證據有三種可能：查到接收紀錄、確認沒有接收紀錄，或查不到任何資料（只能記為 unknown）。補送契約與去重規則也沒有，所以補送授權不成立。來源：applicability.md「缺件與決策」。
- 補送前至少要有：接收端確認未收到、獨立的補送方法，以及接收端去重契約。

**需要誰決定**
- 服務維護者（Owner 未指名，不編造人名）：確認查詢來源與部署版本。
- 有權接受重複通知風險的人：決定補送條件。
- 以上是教學包建議的分工，不是公司已採用的規範。來源：applicability.md。

## 執行與判讀核對

兩種輸入各三次均完成、輸入未變；是否自行指定補送 ID 由作者逐份閱讀判定。這是第一組出現差異後的追加查核，不是事前註冊的實驗。模型未連外查 Log、未執行補送。

## 十次實跑的組成

| 查核 | 次數 | 與本篇的關係 |
|---|---:|---|
| 舊設計說法＋現行程式 | 1 | 背景查核：Claude 可從程式更正舊說法 |
| 作者 Wiki＋現行程式 | 1 | 本文發現漏寫同步通知分支 |
| 問另一版本但未提供程式 | 1 | 背景查核：另一版本留為未知 |
| 接受修訂後，開新對話 | 1 | 本文確認新知識被讀取，部署版本仍未獨立證明 |
| 工單，未加／加上使用條件頁 | 各 3 | 本文六份回答比較；後四次為追加查核 |


## 補充對照：完全不提供 Wiki

同樣工單、事件、程式、提示與工具設定，刻意不提供Wiki，三次獨立對話。提示仍要求從INDEX找知識，因此模型先發現缺檔再改查程式；這不是隨機受控實驗，不用來估準確率。

### 不提供 Wiki，第 1 次

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

### 不提供 Wiki，第 2 次

**結論：目前不建議補送，也不能判定漏送。**

**注意：** `wiki/INDEX.md` 不存在，所以沒有 wiki 可選。我改讀 `sources/` 的原始碼，結論全部來自 `Program.cs`、`Cancellation.cs`、`design-review.md` 和兩個 JSON。

**已確認**
- 事件 `notify_sent` 帶 `sync:true`（`sender-event.json`）。程式裡只有 `SendOnce` 會寫這個欄位（`Program.cs:222`）。
- `SendOnce` 只在 `faults.SyncNotify` 為真時被呼叫（`Program.cs:85-86`），這個旗標來自 `OC_FAULTS` 檔（`Program.cs:190`）。
- `notify_sent` 只代表接收端回了 2xx（`Program.cs:217,222`），不代表使用者收到。
- 事件有 `notification_id`，表示這次取消確實發生了狀態轉換（`Program.cs:79-83`、`Cancellation.cs:25`）。
- 重複取消和已出貨都不會通知（`Program.cs:74-76`）。
- `fixture` 欄位標明事件是「SYNTHETIC」，並非實際擷取的 log（`sender-event.json`）。

**尚缺**
- 接收端 log 和部署設定證明（`ticket.json` 的 `available`）。
- 實際生效的 `OC_FAULTS` 和 `OC_SINK_URL`，所以無法證明部署是否走同步路徑。
- `/version` 固定回 `notification_mode="async"`（`Program.cs:37`），不能拿來當設定證據。
- 補送契約和具名 Owner（`ticket.json`）。
- `design-review.md:9` 說本輪沒跑 .NET，行為未實測。

**下一步查哪裡、用什麼條件**
1. 查接收端 log：`notification_id=demo-notify-18`，並用 `order_id=demo-order-18` 交叉比對，時間窗 `2026-10-01T00:00:00Z/00:05:00Z`。有收據就問題在接收端之後；沒有收據才是接收端缺漏。
2. 查寄件端 `logs.jsonl`：同一個 `notification_id` 是否有 `notify_attempt_failed` 或 `notify_dead_letter`。
3. 確認部署的 `OC_SINK_URL` 是否指向真實接收端還是 fake sink，以及版本是否為 `delivery-hardening-local-r2`。

**是否可補送**
不可以。接收端沒有確認缺漏，也沒有補送契約。程式碼裡沒有補送入口，也沒有去重保證，貿然重送可能造成重複通知。

**需要誰決定**
需要「補送契約的 Owner」。工單沒有指名，我不替任何人猜測。請先請工單提出者指定。

### 不提供 Wiki，第 3 次

**注意:** `wiki/INDEX.md` 不存在,所以我沒有選到 wiki 知識。以下只根據 ticket.json、sender-event.json 和 `sources/` 下的程式與設計核對,不含 wiki 結論。

**已確認**
- 事件是 `notify_sent`,`sync:true`,帶有 order_id 和 notification_id(sender-event.json)。它是合成 fixture,不是實際擷取的 log(同檔 `fixture` 欄)。
- `sync:true` 只出現在 `SendOnce`,且只有 `faults.SyncNotify` 開啟才會走這條路(Program.cs:85-86、222)。
- 這個事件只代表送出端收到 sink 的 2xx(Program.cs:216-217、222)。它不證明使用者端收到通知。
- 取消 API 回 200 不代表通知成功。同步路徑就算進 dead_letter 也照回 200(Program.cs:90-93)。

**尚缺**
- 接收端 log、部署設定證明、補送合約、具名 Owner 都沒提供(ticket.json `available`)。
- 實際部署是否開了 `sync_notify`,以及 `OC_FAULTS` 內容,都沒有證據。`/version` 寫死回 `async`(Program.cs:37),不能拿來當佐證。
- `demo-notify-18` 不是程式產生的格式(程式用 Guid N,Program.cs:82),需確認 ID 對應。

**下一步查哪裡、用什麼條件**
1. 接收端:查 notification_id=`demo-notify-18` 或 order_id=`demo-order-18`,時間 2026-10-01T00:00Z–00:05Z,看收據次數和 payload。
2. 送出端 `logs.jsonl`:找同 order_id 的 `cancel` 事件,確認 `transitioned=true` 且 notification_id 一致。再確認同 ID 沒有 `notify_attempt_failed` 或 `notify_dead_letter`。
   - log 的 `ts` 用本機時間(Program.cs:159),比對視窗前要先換算成 UTC。
3. 部署:取得 `OC_FAULTS` 檔、`VERSION` 檔、`OC_SINK_URL`,核對是否為 `delivery-hardening-local-r2`。

**是否可補送**
目前不能判定,也不建議補送。
- 程式沒有補送入口,也沒有補送合約,接收端是否以 notification_id 去重也不明。
- 若接收端已收到,補送可能造成重複通知。
- 只有接收端查無此 ID,而且合約允許時,才能考慮補送。

**需要誰決定**
補送合約和去重規則需要 Owner 決定,但 ticket 沒有指名。我不編造人選,請先確認 Owner 是誰。接收端 log 和部署設定則需要各自的持有者提供。

**來源:** ticket.json、sender-event.json、sources/Program.cs、sources/design-review.md(第 7 點:本輪未跑 .NET,相關測試仍是待執行設計)。
