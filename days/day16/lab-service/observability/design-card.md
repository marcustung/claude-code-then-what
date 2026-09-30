# Telemetry Design Card｜order-cancel-lifecycle

建立 2026-09-24。來源：`specs/rules-v2.md`（BR-01～04、SC-01～07）與 `specs/notification-contract-v2.1.md`（NC-01～07）。
**原則：觀測點不是從「有什麼指標可以收」倒推，是從「規格說了什麼算完成」正推。** 規格沒定義的東西，收了也沒有判準。

## 一、從規則推訊號

| 規格條目 | 它主張什麼 | 對應訊號 | 真相來源 | 成熟時間 |
|---|---|---|---|---|
| BR-01／SC-01、03、04 | 可取消的訂單會被取消 | `oc_cancel_requests_total{result="ok"}`、`oc_transitions_total` | 服務自身 | 即時 |
| BR-02／SC-02、05 | 已出貨的不可取消，且不丟例外 | `oc_cancel_requests_total{result="rejected_shipped"}`、HTTP 409 | 服務自身 | 即時 |
| BR-04／SC-06、07 | 重複取消維持原狀 | `oc_cancel_requests_total{result="idempotent"}` | 服務自身 | 即時 |
| NC-01 | 每次真實轉換恰好一則通知 | `oc_notify_enqueued_total` ÷ `oc_transitions_total` | 服務自身 | 即時 |
| NC-04 | **送達以接收端收據為準** | `receipts.jsonl` 的唯一 `notification_id` | **接收端（FakeSink）** | **要等佇列排空** |
| NC-05 | 失敗要重試，超限進 dead_letter | `oc_notify_failed_total`、`oc_notify_dead_letter_total` | 服務自身 | 退避三次後 |
| NC-07 | 版本可追溯 | `oc_info{version}`、每筆 log 帶 version | 服務自身 | 即時 |

## 二、三個層次不能互相代替（NC-04）

```
API 接受          狀態已改          通知送達
HTTP 2xx 且       GET 回            接收端有收據
transitioned=true Cancelled=true    receipts.jsonl
     │                 │                 │
  服務自己說        服務自己說        別人說
```

`oc_notify_sent_total` 是服務自己記的「我送出去了」，**不算送達證據**。
後續 的對帳只認第三欄。這條在 `slo/rules.json` 是 SLI-02。

## 三、每個訊號的「什麼時候能讀」

這一欄是最容易被跳過、也最容易出事的：

| 訊號 | 太早讀會怎樣 | 判準 |
|---|---|---|
| `oc_transitions_total` | 不會錯，轉換是同步的 | 隨時 |
| 收據對帳（SLI-02） | **佇列還沒排空時，會把「在路上」讀成「掉了」** | `oc_notify_queue_depth == 0` 才成立 |
| `oc_gc_heap_bytes` 成長 | 只跑 20 次呼叫時，量到的是 JIT 暖機不是洩漏 | 只在 `mode=load` 的 run 成立 |
| `oc_request_latency_ms` 分位數 | 樣本全擠在第一個桶時，輸出是內插不是量測 | 第一桶佔比 < 60% 才可信 |

實例：`slow-sync-control-20260923-191636` 轉換 259、收據 12，看起來掉了 247 則；
同一個 run 結束時 `oc_notify_queue_depth = 253`——**通知在佇列裡，不是掉了**。
對帳讀早了 39 秒（259 則 × 150 ms 的慢接收端），結論就會整個相反。

## 四、連 Claude 自己也要被觀測

服務的訊號回答「系統做得對不對」，但這個 repo 裡有一半的改動是 Claude 寫的。
**改動本身也要有訊號**，否則出事時查不出是哪一版、由誰改的：

| 要回答什麼 | 訊號 | 位置 |
|---|---|---|
| 這次 run 跑的是哪一份 Domain？ | `domain_sha256`、`api_sha256` | 每個 run 的 `manifest.json` |
| 這一版改了什麼、誰接受的？ | `decisions-v*.md`、`CHANGELOG.md` | `specs/`、repo 根 |
| Claude 這次用了哪些工具、跑多久？ | `worklog.jsonl` | `evidence/worklog.jsonl` |
| 情境檔本身有沒有被動過？ | `scenario_sha256` | 每個 run 的 `manifest.json` |

沒有 `domain_sha256`，「v1.1 有問題、v1.2 修好了」就只是說法；
有了它，`evidence/runs/*/manifest.json` 可以把每一個結論對回確切的程式位元。

## 五、規格沒說的，這張卡不收

2026-09-24 我把 `specs/` 與 `src/Api/Program.cs` 交給 Claude Code（只讀工具），請它獨立從規格正推一次觀測點，再回頭對照程式實際輸出了什麼。它列出**五類「有收但規格沒有判準」**，比我原本寫的多三類：

| 訊號 | 規格狀態 |
|---|---|
| `oc_gc_heap_bytes`、`oc_working_set_bytes`、`oc_gc_collections_gen2` | 兩份規格都沒提；是 OOM 事故之後加的 |
| `oc_request_latency_ms` 直方圖 | 規格沒訂任何延遲門檻，只是有收 |
| `oc_notify_queue_depth` | 契約**要求要收**，但沒有訂「多少算積壓」 |
| `notify_deferred_total`、`MaxDeferrals=5` | 契約裡沒有 deferral 這個概念，是實作自訂 |
| `oc_cancel_requests_total{result="unauthorized"}` | **BR-01～04 沒有任何一條定義 401** |

最後一列是真的缺口，不只是沒訂門檻：`rules-v2.md` 全文沒有 401 或 404，但 `scenarios/baseline.json` 的 `expected` 寫著 `unauthorized: 1`、`not_found: 1`，程式也真的實作了。**情境檔在斷言一個規格從未定義的行為**，而我在 `slo/rules.json` 把 SLI-01 的來源標成 `spec`——標錯了，已改為 `mixed`。

它還指出一件我沒寫進卡裡的事：NC-01／NC-04 的對帳等式第三項（接收端收據）**完全在這個服務之外**，`Program.cs` 沒有讀寫 `receipts.jsonl` 的任何一行。所以這個服務**在結構上就不可能自己證明通知送達了**——對帳一定要有外部腳本。這正是第二節那張圖想講的，但原本沒講到「服務自己做不到」這一層。



`oc_working_set_bytes`、`oc_gc_collections_gen2` 有收，但**不設門檻**：
規格沒有定義它們多少算好。它們只用來解釋別的訊號為什麼動，不單獨觸發告警。
這是刻意的——**沒有判準的指標一旦接上告警，就只會製造雜訊。**
