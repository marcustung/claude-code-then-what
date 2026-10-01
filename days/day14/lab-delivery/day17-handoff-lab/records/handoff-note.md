以下路徑都在 `runs/` 底下。故障期間的原訂單是 `during-update`，通知 ID 為 `d0e39019500e489cb21d391c3f303b05`。

## 1. 服務已恢復的依據

服務在本機演練中已恢復。這只涵蓋服務本身，不涵蓋訂單。

- **版本已回到 r1**：`acceptance-rollback-01/requests.json:115-123` 顯示 rolled-back 階段的 `/health` 回 200，版本為 `delivery-hardening-local-r1`。`rolled-back/logs.jsonl:1` 的 startup 事件版本也是 r1。
- **套件是原本的候選版**：`report.json` 的 `checks[rolled-back-package]` 為 `candidate-checked`。`rolled-back/deployment.json:2-14` 有套件雜湊，`:15` 記錄假接收端已回到 200。
- **新的探測請求成功送達**：
  - 訂單 `after-rollback` 取消回 200（`requests.json:156-175`）。
  - 收據 `receipts.json:72-84` 顯示接收端回 200。
  - 日誌 `rolled-back/logs.jsonl:3` 有 `notify_sent`。
- **故障確實發生過**：`updated/logs.jsonl:3-7` 顯示 4 次 503，之後出現 `notify_dead_letter`。`incident.json:17-19` 記錄 attempts 為 4、接收端狀態 503。
- **整體驗收**：`report.json` 的 `passed` 為 true。

限制：`report.json` 的 `limits` 寫明這是作者自己操作的本機演練，沒有正式部署。兩份接手單的 `service` 欄位（`handoff.json:41`）也只寫「restored in local rehearsal」。

## 2. 仍不能補送或結案的原因

- **訂單在回滾後查不到**：`requests.json:137-140` 對 `during-update` 查詢回 404。`report.json` 的 `rollback-does-not-restore-orders` 也是 404。訂單存在程序記憶體，重啟後就沒了。這是教學環境的設計，不是新缺陷。
- **沒有可重送的來源**：兩份接手單 `handoff.json:42` 寫「no persisted notification replay source」。通知只留下失敗的 dead letter 紀錄，沒有可重送的內容。
- **原本的取消與退款請求沒有送達下游**：
  - `receipts.json:16-71` 顯示原通知 4 次都得到 503。
  - 該通知的 `refund_requested` 為 true。
  - API 當時已回 200 並標成已取消（`requests.json:94-113`），但下游沒有收到。
  - 4 次 503 是人為注入的假接收端回應，不是程式缺陷（`incident.json:20`）。
- **政策明確禁止的動作**：`handoff.json:35-39` 禁止重建訂單、重送通知、宣告業務對帳完成。`incident.json:22` 也寫明不重播失敗訂單。
- **沒有人接手**：兩份接手單的 `owner_acknowledged` 都是 false（`:47`），`close_condition`（`:50`）「not fulfilled here」。
- **兩份接手單的差別只在時間**：
  - wait 單的狀態是 `WAITING_FOR_OWNER`，經過秒數為 0。
  - escalate 單的狀態是 `ESCALATE`，經過秒數為 300。
  - 時間是模擬參數，沒有真人等待。`external_notification_sent` 為 false，沒有通知任何人。
  - 300 秒只是教學範例，不是公司的服務水準承諾（`policy.deadline_is`）。

## 3. 下一位接手者需要確認的問題

以下事項都不是我能決定的，也沒有任何一項已被處置。

| 問題 | 查哪個來源 | 誰決定、缺什麼 |
|---|---|---|
| 這張單現在由誰負責？ | `handoff.json:27-28` 只有角色，沒有姓名，且註明「must assign a real person」 | 組織需要指派值班人和服務負責人；缺的是真實人員名單。 |
| 原訂單的真實業務狀態是什麼（是否已付款、已出貨、已取消）？ | 訂單記憶體已遺失。要查訂單來源系統或客戶端請求紀錄，這個目錄裡沒有這些資料。 | 已授權的負責人決定；缺原始訂單資料。 |
| 退款是否已被下游處理，還是沒收到？ | 下游接收端的實際紀錄。本目錄只有假接收端的 503（`receipts.json`），看不出真實下游狀態。 | 已授權的負責人；缺下游的實際結果。 |
| 是否要補送或重建？ | 目前沒有可用的補送來源（`handoff.json:42`）。 | 授權人決定。決定前需要知道訂單真實狀態、下游是否已處理，以及重送是否會造成重複退款。這幾項都還沒有答案。 |
| 訂單遺失後，客戶端看到「已取消」是否需要更正或告知？ | `requests.json:94-113` 顯示 API 曾回 200 且 `cancelled: true`。 | 業務負責人決定；缺客戶端實際看到的內容。 |
| 何時才算結案？ | `handoff.json:50` 的 `close_condition`：授權負責人確認原業務狀態與下游結果。 | 只有該負責人能宣告；目前條件未滿足。 |

接手者現在可以做的事，只有政策允許的兩項（`handoff.json:31-34`）：讀取請求、日誌、收據，以及查證已部署版本並發出新的探測。

另外，`incident.json:24` 的 `acceptance` 是「服務已恢復，且未解決的訂單被明確保留」。這是演練的驗收條件，不代表業務已對帳。