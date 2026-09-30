# Day 16 操作附件｜版本演練、唯讀查核與補測

本附件保存正文省略的操作細節。這些是既有本機實跑的紀錄，不代表重新執行，也沒有正式部署。

[回到正文](https://ithelp.ithome.com.tw/articles/10419105)

## 先分清楚這幾輪

| 原件目錄（examples/sdlc-delivery 下） | 用途 |
|---|---|
| `runs/acceptance-next-01` | r2 的檢查與發布包 |
| `runs/acceptance-rollback-01` | 舊版、新版故障、恢復舊版三段演練與十八項斷言 |
| `day16-design-trace-01` | Claude 讀設計核對文字、演練與新版程式，核對路徑與涵蓋範圍 |
| `day16-rollback-lab` | Claude 分開判讀程式、下游與原訂單狀態，提出補測 |
| `runs/r2-healthy-01` | r2 搭健康接收端的十項補測 |

系列公開 repo 對應入口是 `days/day14/lab-delivery/`。這些輪次共用服務，但版本與條件不同，不能合併成同一份發布包的所有成效。

## 版本與演練細節

## 新版改了什麼，先說清楚

舊包是前兩篇使用的 `candidate-checked`，版本 `delivery-hardening-local-r1`。新版 `release-next` 新增一個 `GET /version`：除了版本，也回傳非同步通知與記憶體儲存的特性，讓接手者可以直接查，不必翻原始碼。

```json
{
  "version": "delivery-hardening-local-r2",
  "notification_mode": "async",
  "storage": "in-memory"
}
```

本次新增入口與演練程式是在備稿時建立，不是 Claude 自動更新的成果。這是一項真正的 API 變更，不是只改版本文字。取消規則保持原樣。新版重新經過既有 CI、81 項並行檢查、發布與 10 項產物 smoke，才留下 `acceptance-next-01/package`。

演練腳本會在本機依序啟動舊包、新包、再回復舊包，記錄版本與請求；它只操作自己建立的程序與假接收端，不碰正式環境。完整命令與設定以對應執行目錄為準。

## 程式起來了，通知卻沒有完成

演練先用 r1 建一張訂單並取消，接收端回 200，留下 `notify_sent`。

接著停止 r1、啟動 r2。`/health` 回 200，`/version` 也顯示新版。但這一段我刻意讓假通知接收端回 503，模擬更新時遇到下游不可用。

新訂單的取消 API 仍回 200。通知背景程序則嘗試四次，全收到 503，最後留下 `notify_dead_letter`。這個名字在本服務代表失敗終態的日誌，沒有一個可持久化、按一下就能重新投遞的佇列。

如果只看健康檢查，更新像是成功了。沿著一張新訂單走到通知結果，才知道服務的工作沒有全做完。

故障是本次刻意注入的接收端回應，不是查出 `/version` 新功能造成了錯誤，也不是生產事故。

## 先用紀錄核對三件事，再請 Claude 找缺口

這一節到上一節為止都是腳本跑、我自己判的，還沒交給 Claude。先把我查到的攤開，後面兩讀才有東西可以對照。

演練觸發停止條件後，停止 r2，回到原本的 r1 包，並把假接收端恢復成 200。**本次同時恢復程式與接收端條件，不能把恢復成果全歸功於換回程式。**

| 核對項目 | 更新到 r2 | 回復 r1 |
|---|---|---|
| 實際版本 | `/health` 顯示 r2，新 `/version` 可用 | `/health` 顯示 r1，新入口回 404 |
| 新建訂單能否完成工作 | 取消 200，通知四次 503 後失敗 | 另一張新訂單取消成功，通知也收到 |
| 重啟前的訂單 | 原 r1 訂單回 404 | r2 故障期間的訂單也回 404 |

最後一列才是這次演練最值得留下來的事。訂單存在程序記憶體，停止程序就不在了。**新訂單又能工作，不代表故障期間那張訂單已被處理。**

演練腳本的 18 個自動檢查點全部通過。它們是同一套更新與回復情境裡的斷言，不是 18 起事故，也不是 Claude 自己執行的 18 次查核。下面保留幾個關鍵結果，作為後續判讀的已知基準。

其餘檢查用來核對包身分、版本與各階段請求結果；不同階段包含成功與刻意注入的失敗，不能統稱為服務正常。

另外六項觀察更新與回復前後的狀態：

| 檢查 | 結果 | 它在問什麼 |
|---|---|---|
| `update-loses-memory-state` | 404 | 停啟之後，舊資料還在嗎 |
| `failure-detected` | `notify_dead_letter` | 失敗有沒有落到終態 |
| `failure-four-attempts` | 4 | 重試幾次才放棄 |
| `old-endpoint-restored` | 404 | 退回後新功能確實消失了嗎 |
| `rollback-does-not-restore-orders` | 404 | 退回程式會不會把資料帶回來 |
| `failed-order-not-replayed` | `no automatic replay` | 沒人處理的那筆會不會自己好 |

**三個 404 都記成通過項。**這裡預期舊入口或記憶體資料會消失，因此查到 404 代表符合演練預期；不代表資料消失是可以接受的產品行為。判讀綠燈之前，要先看這一項究竟在驗什麼。

所以 `report.json` 寫著 `passed: true`，結論卻是資料沒回來、那筆訂單沒人處理。通過代表演練把邊界查清楚，不代表資料遺失可以接受，更不代表服務已具備上線條件。

演練真正交出去的不是綠燈，是這張缺口清單：要讓真正的訂單服務上線，還得有持久化、資料結構相容性、通知保存與恢復策略。這些不能靠一句「Claude，幫我退回上一版」補完。

到這裡三件事都查清楚了，十八項也都過了，答案是我自己下的。問題是我只會看到我想得到的東西。

所以我把同一份紀錄交給 Claude 讀兩次。**第一讀帶著 Day 10 的設計核對，問它這筆工作沿著設計停在哪裡；第二讀只給紀錄，問它程式、下游、故障期資料各自恢復了沒有。**兩次都唯讀、都要求附出處，兩次都指出一段我沒驗到的路。


## Claude 怎麼讀，哪些結論不能算成它的發現

第一輪有設計核對文字，沒有原圖；第二輪讀演練紀錄與相關程式。保存的提示本來就要求區分恢復範圍，並提醒 `passed: true` 不等於可上線，不能把這些前提寫成模型獨立發現。

兩輪工具設定限制為 `Read`、`Grep`、`Glob`，不開 `Edit` 或 `Bash`，清空其他設定來源並使用空 MCP 設定。以下是歷史執行配置的摘要；完整可核對命令以各輪保存紀錄為準。

```sh
claude -p "<查核提示>" --restricted \
  --tools Read,Grep,Glob --allowedTools Read,Grep,Glob \
  --setting-sources '' --strict-mcp-config --mcp-config empty-mcp.json \
  --no-session-persistence --max-budget-usd 3
```

這限制模型可呼叫的工具，不是把檔案系統縮成幾個檔案的沙箱。執行器寫出的 `changed: []` 也不能單獨當成前後檔案未變動的證明；查核應以實際工具軌跡與可比對的檔案內容為依據。

第一輪指出設計行號過期，以及本輪未涵蓋的設計項目：已出貨拒絕、並行安全、payload 風險與決策表沿用。作者複查了行號與六筆訂單皆未出貨；不能把其他模型推論都視為人工驗證完畢。

## 補測的十項到底是什麼

`verify-r2-healthy.py` 是補測腳本，結果保存在 `runs/r2-healthy-01/report.json`。它啟動 r2 配健康接收端，檢查：包身分、健康版本、新入口、取消成功、通知送達、首次嘗試成功、通知 payload 旗標、程序運行時訂單可查、已出貨拒絕取消，以及拒絕後沒有新增通知。

這是十項斷言，並非十次獨立負載實驗。接收端收到通知的紀錄與 `notify_sent` 相互核對；未補送故障期間原通知，未驗證長時間穩定性與並行安全。

重跑前要先查看腳本的參數與程序管理方式，使用隔離的本機埠與假下游。不要把歷史結果檔改成新一輪結果，也不要把這套記憶體儲存範例直接當作正式服務。

## 接手單與升級狀態的驗證

既有 `prepare-handoff.py` 讀事件與接收端紀錄，產生接手資料。以下以參數模擬經過時間，沒有真的等五分鐘，也沒有傳送通知：

```sh
python prepare-handoff.py acceptance-rollback-01 --elapsed-seconds 0 --output my-wait
python prepare-handoff.py acceptance-rollback-01 --elapsed-seconds 300 --output my-escalate
```

原件 `runs/acceptance-handoff-wait` 為等待，`runs/acceptance-handoff-escalate` 為升級；升級結果仍為 `owner_acknowledged=false`、`external_notification_sent=false`。五分鐘是教學政策，不是公司 SLA 或實測應答時間。

Claude 的既有唯讀核對保存在 `day17-handoff-lab/records`：`prompt.txt`、`trace.jsonl`、`handoff-note.md` 與 `tools-used.json`。本次只把結果收進 Day16，沒有重新執行或修改原件。通知、真人接受與原通知補送都未完成。
