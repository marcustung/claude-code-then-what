# 訂單取消 API 效能測試策略（獨立規劃）

> 依 skill 工作流程完成之產出。**MCP 研究步驟不可用**：本次未執行 `mcp_k6_info` 或 `mcp_k6_search_documentation`，因此無法確認實際安裝的 k6 版本細節或查證特定模組/API 文件；下列 k6 執行器與模組名稱僅基於既有知識假設 k6 1.3.0 相容，執行前建議自行核對官方文件。本輪僅完成規劃，未讀取/執行/修改任何測試腳本或服務程式碼，也沒有既有測試計畫或歷史結果可供參考。

## 1. 缺失的輸入（Missing Inputs）

在能撰寫具體 k6 腳本之前，以下資訊在現有素材中沒有交代，必須先確認或明確標記為未知：

| 缺口 | 說明 |
|---|---|
| Base URL / Port | `Program.cs` 未寫死 port，需知道啟動時實際監聽位址 |
| 服務是否已在跑 | 未被告知服務目前是否已啟動、以何種環境變數啟動 |
| `OC_FAULTS` 內容 | 若設定檔存在，`DropOverQueue` / `DelayMs` / `RetainPayloads` / `SyncNotify` 都會改變效能與通知行為；目前未知是否啟用 |
| `OC_SINK_URL` / fake sink 行為 | 通知會 POST 到此位址並重試（200/400/800ms 退避）；sink 的延遲、成功率、是否運行未知 |
| `OC_TEST_DELAY_MS` | 若設定，會在取消流程中插入延遲，放大 race window；預設關閉，但目前未知 |
| 版本（`VERSION` 檔 / `OC_VERSION`） | `Retained` 的有界修復是 v1.2.0 之後才有；若跑的是舊版行為會不同，目前無法確認目前部署版本 |
| 測試資料 seed 方式 | 必須先 `POST /orders` 建單才能取消；目前沒有既定 order id 池或建單腳本 |
| Header 語意 | `X-Actor` 必填（否則 401）、`X-Request-Id`/`X-Run-Id` 選填但影響 log 追蹤；沒有說明 actor 值該用什麼 |
| 硬體/主機資源 | Windows loopback 環境的 CPU/記憶體規格未知，會直接影響延遲與是否可信地判斷「瓶頸在服務端還是壓測端」 |
| 既有基準或歷史結果 | 明確聲明：本次規劃**沒有**任何先前測試計畫或結果可參照，所有預期都是假設（hypothesis），非既有事實 |

## 2. 測試目標（Goals）

依 brief 與程式碼比對出的行為契約，教學目的的效能驗證目標為：

1. **正確性優先於效能**：先確認業務規則在負載下仍正確（已出貨不可取消 409、已付款未出貨取消一次即要求退款、重複取消不重複通知、每次狀態轉換恰好一則通知）。
2. **延遲基準（教學用，非 SLA）**：首次取消（transition）路徑 p95 < 250ms。
3. **零失敗率**：預期成功的工作負載（合法 actor、存在的訂單、未出貨）HTTP 失敗率應為 0。
4. **無漏迭代**：k6 iteration 不應被 drop（表示壓測工具本身未過載，量測才可信）。
5. **通知一致性**：`transitions_total` 應等於（`notify_sent_total` + 尚在退避/佇列中未完成的數量），且無非預期的 `notify_dead_letter_total`（在未注入故障的前提下）。

## 3. 風險與已知限制（Risks）

- **記憶體內單例儲存 + `lock`**：`OrderStore.TryCancel` 用單一全域 lock 保護整個字典，高併發下所有取消請求會序列化，這是效能上限的主要嫌疑點，需在報告中如實標註，不可過早下瓶頸結論。
- **通知走非同步 unbounded Channel**：若未設定 `DropOverQueue`，佇列理論上可無限增長；若 sink 慢，`oc_notify_queue_depth` 可能持續上升而不被目前的固定成功條件捕捉到，需另外觀察。
- **`Retained.Keep` 故障注入**：若 `OC_FAULTS.retain_payloads=true`，每筆 request body 會被保留（即使 v1.2.0 後已有界，256 筆 × 256 字元），非本次測試目的但若誤啟用會混淆延遲判讀。
- **`SyncNotify` 故障**：若開啟，通知會同步阻塞在請求路徑上（含最多 3 次重試、最長 1.4 秒退避），會讓 p95 目標直接失真；必須先確認未啟用。
- **單一 .NET 行程、單機 loopback**：無法代表任何生產流量型態；任何觀察都只是「這台機器這個當下的行為」，不可外推為容量規劃結論。
- **無 MCP／無文件查證**：本規劃引用的 k6 語法/模組（如 `http`、`check`、thresholds、executor 名稱）基於既有知識，未經官方文件核對，執行前需人工確認相容 k6 1.3.0。
- **冷啟動影響**：.NET JIT/GC warm-up 可能讓最初幾秒延遲偏高，需要在分析時區分 warm-up 與穩態。

## 4. 優先順序測試矩陣（Prioritized Test Matrix）

| 優先序 | 目標 | 測試類型 | 對應端點 | 關鍵參數（提案，待執行前確認） | 備註 |
|---|---|---|---|---|---|
| P0 | 確認服務可用、業務規則正確（單一/低併發） | Smoke | `/health`, `/ready`, `POST /orders`, `POST /orders/{id}/cancel` | 1 VU、少量迭代 | 必須先跑過才有資格做任何負載測試 |
| P1 | 驗證預期成功工作負載下的延遲與失敗率（**本輪唯一建議執行的實驗**） | Load（bounded） | `POST /orders/{id}/cancel`（已付款未出貨） | 見第 5 節 | 對應 brief 的預先宣告教學標準 |
| P2 | 驗證已出貨拒絕、重複取消冪等（不重複通知）在併發下仍正確 | Load（行為導向，非純延遲） | `POST /orders/{id}/cancel`（shipped=true 與重複呼叫混合） | 需與 P1 分開跑，避免資料互相污染 | 本輪不執行，僅列入未來矩陣 |
| P3 | 找出 lock 序列化 / 通知佇列的臨界點 | Stress / Spike | 同上 | 逐步升 VU 直到 p95 明顯劣化或錯誤率上升 | 超出本輪 60 秒 / 50 VU 預算，需另案批准 |
| P4 | 長時間佇列/記憶體行為（`oc_gc_heap_bytes`、`notify_queue_depth` 是否持續增長） | Soak | 同上 + `/metrics` 輪詢 | 長時間（分鐘～小時級） | brief 明確排除：「Longer soak is outside this run」 |
| P5 | 故障注入情境下的行為（`sync_notify`、`drop_over_queue`、`retain_payloads`） | Load + Fault injection | 同上 + `OC_FAULTS` | 需與服務端協調啟用 fault 檔 | 屬於演練/教學情境，非本輪範圍，且會改變前提條件 |

排序原則：先 smoke 驗證可用性與正確性，再做「有界」的 load 取得延遲基準，最後才考慮 stress/soak/fault 情境（皆超出本輪預算或明確被排除）。

## 5. 建議的唯一具體有界實驗（ONE Concrete Bounded Experiment）

**名稱（建議）**：`cancel-first-transition-load-bounded`

**類型**：Load test（constant-arrival-rate 或等效有界執行器）

**範圍限制（依 brief 預算，不可超過）**：
- 負載時間 ≤ 60 秒
- 新建訂單速率 ≤ 10 orders/sec
- 最大 VU ≤ 50
- 負載結束後 drain（排空）觀察 ≤ 20 秒

**設計**：
1. **Setup 階段**（不計入負載窗口）：以少量請求 `POST /orders` 建立 N 筆訂單，狀態固定為 `shipped=false, paid=true`（對應「已付款未出貨」路徑，會觸發 `refund_requested=true` 與一則通知）。N 應等於負載窗口內預期的取消請求數（≤ 60s × 10/s = 600 筆上限），每筆 order id 唯一，避免與冪等路徑混淆。
2. **負載階段**：對這批訂單各發一次 `POST /orders/{id}/cancel`，帶合法 `X-Actor`、`X-Request-Id`（唯一）、`X-Run-Id`（本次執行識別）。到達率 ≤ 10/s，VU ≤ 50，時長 ≤ 60s。每筆都是「首次取消」（transition），對齊 brief 的 p95 標準。
3. **Drain 階段**：負載結束後，暫停送新請求，改為輪詢 `GET /metrics`，最長 20 秒，觀察 `oc_notify_sent_total` 是否追上 `oc_transitions_total`，且 `oc_notify_dead_letter_total` 維持為 0。

**每次請求的行為檢查（check）**：
- HTTP status 200
- 回應 `ok=true`、`transitioned=true`、`refund_requested=true`（因為固定用 paid+unshipped 訂單）
- `notification_id` 非空

**預期觀察（Expected Observations，皆為假設，待驗證）**：
- p95 延遲 < 250ms（brief 預先宣告的教學標準，非生產 SLA）
- HTTP 失敗率 = 0
- k6 dropped iterations = 0
- Drain 結束時 `notify_sent_total` 增量 = 本次負載中 transition 的訂單數；`notify_dead_letter_total` 增量 = 0
- `oc_notify_queue_depth` 在 drain 結束時應回落到接近 0（若持續偏高，代表通知端處理速度跟不上，屬於需要另案調查的訊號，不在本輪判定範圍內）

**證據（Evidence to collect）**：
- k6 內建摘要：http_req_duration（p95/p99）、http_req_failed rate、iterations/dropped_iterations
- 服務端 `logs.jsonl` 中對應 `run_id` 的 `cancel` 與 `notify_sent` 事件（用於交叉核對通知是否真的送達，而非只信任服務回應）
- 負載前後各一次 `GET /metrics` 快照（用於算 delta，尤其是 `oc_notify_sent_total`、`oc_notify_dead_letter_total`、`oc_gc_heap_bytes`）

**停止規則（Stop Rules，執行中應中止的條件）**：
- 任一時間點 HTTP 失敗率 > 5%（表示行為已偏離「預期成功工作負載」前提，繼續跑只會污染資料）
- k6 回報 dropped iterations > 0（表示壓測端本身已過載，資料不可信）
- 觀察到非預期的 401/404（表示 setup 未正確建單或 header 缺失，屬設定錯誤而非效能訊號，應停止並修正腳本）
- 超過本節列出的任一預算上限（時間、速率、VU、drain 秒數）
- 服務端 log 出現 `unhandled_exception`（表示觸及未預期的例外路徑，應停止分析原因，不應以繞過方式繼續加壓）

## 6. 驗收標準（Acceptance Criteria）

本輪實驗僅用 brief 中**預先宣告的教學標準**作為驗收依據，明確標註「非生產承諾」：

- [ ] 首次取消（transition）請求的 p95 延遲 < 250ms
- [ ] 預期成功工作負載的 HTTP 失敗率 = 0
- [ ] 所有行為 check（status、`transitioned`、`refund_requested`、`notification_id`）100% 通過
- [ ] 無 dropped iterations

任何超出上述四項以外的觀察（例如佇列深度、GC 行為、通知送達延遲）只能列為**待驗證假設**，不得在本輪直接判定通過/失敗，因為沒有既有 SLA 或歷史基準可比對。

## 7. 下一步

若同意上述唯一實驗的範圍，我可以：
1. 邀請你確認第 1 節「缺失的輸入」中至少 base URL、`OC_FAULTS` 狀態、actor 值後，
2. 再呼叫對應的 k6 測試撰寫 skill（load test）產生實際腳本——**本輪僅規劃，未撰寫或執行任何腳本**。