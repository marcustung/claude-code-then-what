# Day 23：Claude 對照 v1.0.0 程式與故障紀錄（2026-10-07）

- 模型 Sonnet（`claude -p --model sonnet`），工具只開 Read／Grep／Glob，同一提示跑 3 次；提示見 `prompt.txt`。
- 工作目錄 `ws/`：`git archive 71e57b8`（v1.0.0）＋`specs/notification-contract-v2.1.md`＋故障那輪 `missing-notification-20260921-193704` 的 requests／logs／metrics／receipts／manifest（放在 `ws/run/`）。

## 去洩漏（給模型前移除或改名）

- 刪除：`evidence/`（含 check.json）、`CHANGELOG.md`、`scenarios/`、`tools/`（含 check.py）。
- `src/Api/Program.cs`：刪掉說明故障的註解（「故障 notify_drop_over_queue（演練用）…不再重送，但 sent 計數照加」等 3 行）；`DropOverQueue→QueueLimit`、`notify_drop_over_queue→notify_queue_limit`、`Faults→RuntimeFlags`、`OC_FAULTS→OC_FLAGS`。
- 紀錄：`missing-notification`→`run-a`、`faults_loaded`→`flags_loaded`（四檔一致替換，跨檔 ID 仍對得上）；manifest 刪 `faults_file`、`faults_sha256`。

## 結果（修正副本，r4～r6）

第一版副本刪註解時把 `{   // 故障：假裝送了` 整行刪掉，少了一個左大括號，延後分支的語意與原碼不同；那 3 次（r1～r3）移到 `first-copy-missing-brace/` 保留，不作為本篇證據。補回大括號後，副本扣掉註解與改名與 `git show 71e57b8:src/Api/Program.cs` 逐行一致，再跑 3 次：

| | r4 | r5 | r6 |
|---|---|---|---|
| 回合／秒／US$ | 14／54.5／0.288 | 13／47.8／0.284 | 14／62.5／0.301 |
| 指出延後分支 `Program.cs:143-148` 直接 `continue`、沒有重新執行 | 是 | 是 | 是 |
| 指出 `notify_sent_total` 在延後分支（`:145`）就加一 | 是 | 是 | 是 |
| 9 次轉換只有 3 筆收據、6 則遺失 | 是 | 是 | 是 |
| 指出遺失中有退款通知 | 否 | 否 | 是 |
| 指出 manifest 的完成判準被遺失騙過 | 是 | 是 | 只提 expected 對不上 |

人工核對：依 `r4.md`～`r6.md` 原文逐項確認。限制：同一份資料跑 3 次，教學服務、單一故障；程式結構仍可能透露線索，不估一般準確率。
