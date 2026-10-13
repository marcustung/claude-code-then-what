# 驗收規格：通知送不出時的重送與補償（Day 29 實驗 1）

> 這份規格與 `run_acceptance.py` 是實驗的**考題**。迴圈**不得修改** `acceptance/` 下任何檔案（以雜湊檢查）；只能改 `src/` 讓測試轉綠。

## 背景
目前通知送不出去時，worker 重試 3 次（200／400／800 ms）後只寫一行 `notify_dead_letter` log，通知就此遺失；沒有可查的死信、沒有重送、沒有補償。

## 設定（環境變數）
| 變數 | 意思 | 測試用值 |
|---|---|---|
| `OC_REDELIVERY_INTERVAL_MS` | 死信自動重送的間隔 | 1000 |
| `OC_REDELIVERY_MAX_ROUNDS` | 自動重送的最多輪數，超過即放棄 | 3 |

## 驗收條件

| 編號 | 條件 |
|---|---|
| AT-01 | 接收端掛掉時，重試用盡的通知要進**死信清單**：`GET /admin/dead-letters` 列出 `notification_id`、`order_id`、`attempts`、`last_error`、`status` |
| AT-02 | `/admin/*` 一律要 `X-Actor` header，沒有回 401 |
| AT-03 | 手動重送：`POST /admin/dead-letters/{notification_id}/replay`，接收端恢復時回 200，接收端收到該通知的收據，死信清單不再列出它 |
| AT-04 | 重送是冪等的：已送達的通知再 replay 回 404 或 409，接收端收據仍只有一筆 |
| AT-05 | 自動重送：接收端恢復後，死信在 `INTERVAL × MAX_ROUNDS` 內自動送達，不需手動 replay |
| AT-06 | 放棄：自動重送輪數用盡仍失敗，狀態改為 `abandoned`，`oc_notify_abandoned_total` 遞增，寫 `notify_abandoned` 的 ERROR log |
| AT-07 | `/metrics` 有 `oc_notify_dead_letter_depth`，等於目前死信清單中待重送的筆數；送達後歸零 |
| AT-08 | `oc_notify_sent_total` 只在接收端確認後才遞增：接收端掛掉期間維持 0 |
| AT-09 | 對帳：`GET /admin/reconcile` 回 `transitions`、`delivered`、`pending`、`abandoned`，且 `transitions == delivered + pending + abandoned` |
| AT-10 | 補償：已付款（會退款）的訂單，通知被放棄時，`GET /orders/{id}` 回 `needs_manual_followup: true` |
| AT-11 | 死信要持久化：存在 `OC_RUN_DIR` 下，服務重啟後死信清單仍在 |
| AT-12 | 不退步：既有的 DomainTests 全過；接收端正常時，取消一筆未出貨訂單，通知照常送達 |
