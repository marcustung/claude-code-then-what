# order-cancel-lifecycle｜訂單取消＋通知：同一份程式從開發走到維運

Day 8–30 的共同範例（2026-09-21 起）。.NET 9。**不是公司系統**，所有輸入由 `scenarios/*.json` 固定給定。

核心問題：**取消功能通過測試，使用者卻沒收到通知——開發時的「完成」條件，留下多少維運工作？**

## 這裡有什麼

| 目錄 | 內容 |
|---|---|
| `specs/` | `rules-v1.md`／`decisions-v1.md`（Day 6 教學示範）、`rules-v2.md`（BR-01–04、SC-01–07）、**`notification-contract-v2.1.md`（新需求，NC-01–07，狀態 proposed）**、`decisions-v2.1.md` |
| `src/Domain/` | `Cancellation.Cancel()`（v2 規則）＋`Transitioned()`；三個型別簽名沿 v1 不可改 |
| `src/Api/` | 薄 HTTP API：`POST /orders`、`POST /orders/{id}/cancel`、`GET /orders/{id}`、`/health`、`/ready`、`/metrics`；程序內記憶體；每 request 一行 `logs.jsonl`；通知 worker（重試 3 次、dead_letter） |
| `src/FakeSink/` | 本機假接收端：每則實際收到的通知寫一行 `receipts.jsonl`——**送達的獨立來源** |
| `tests/DomainTests/` | SC-01–07＋NC-01／02，`dotnet run` exit code＝失敗數 |
| `scenarios/` | `baseline.json`（12 單 20 呼叫：重複取消、已出貨、不存在、未授權）、`missing-notification.json`（同輸入＋注入）、`faults/`（**故障答案，診斷者不可見**） |
| `tools/run.ps1` | 可重跑入口：build → 啟 sink／api → readiness → 固定輸入 → 等終態或 timeout → 匯出 → `check.py` → 停止 |
| `tools/check.py` | 三來源對帳：唯一成功轉換 == enqueued == 收據（去重）；服務 `sent_total` 必須等於收據；缺檔／格式錯／timeout／dead_letter → FAIL |
| `diagnosis/` | 盲診：去答案快照、提示、runner、六次輸出與彙整 |
| `knowledge/` | 事故條目與從事故長出的規則（team LLM wiki；`CLAUDE.md` 可 `@knowledge/RULES.md` 匯入） |
| `evidence/runs/` | 每次 run：`requests.jsonl`（客戶端）、`logs.jsonl`（服務）、`receipts.jsonl`（接收端）、`metrics.txt`、`final-states.json`、`manifest.json`（版本、雜湊、人工欄位 null）、`check.json` |

## 第一階段驗收（2026-09-21，AI 執行；作者尚未操作）

| run | 版本 | 終態 | 對帳 | 成功轉換 | 服務自報 sent | 接收端收據 | 延後未送（丟） | 延後重排 |
|---|---|---|---|---|---|---|---|---|
| `baseline-20260921-193610` | 1.0.0 | terminal | **PASS** | 9 | 9 | 9 | 0 | 0 |
| `baseline-20260921-193902` | 1.1.0 | terminal | **PASS** | 9 | 9 | 9 | 0 | 0 |
| `missing-notification-20260921-193704` | 1.0.0 | terminal | **FAIL** | 9 | 9 | 3 | 6 | 0 |
| `missing-notification-20260921-193835` | 1.1.0 | terminal | **PASS** | 9 | 9 | 9 | 0 | 45 |

- **正常通過**：v1.0.0 baseline，9 則轉換、9 則收據、三來源一致。
- **故障被偵測**：v1.0.0 注入 `notify_delay_ms=400 + notify_drop_over_queue=2`（worker 慢、佇列滿時「延後不重送、sent 照加」）——服務說送了 9，接收端只有 3；`check.py` FAIL，指出「計數器說謊 6 則」。
- **修復後通過**：v1.1.0 把壓力路徑改為重排（最多 5 次）、`sent_total` 只在 ack 後加；同一注入下 9／9／9，PASS。延後重排 45 次是壓力的痕跡，不是丟失。
- **正常回歸**：v1.1.0 baseline PASS。

修復由 Claude Code（AI）依對帳結果提出並實作；不是預先安排「一定要失敗一次再修」——v1.0.0 的丟失是注入設計要驗的東西，v1.1.0 是對它的回應。**作者尚未審查或接受**任何一版；`specs/decisions-v2.1.md` 全為 proposed。

## 壓力情境（2026-09-21，AI 執行）

| run | 版本 | 終態 | 檢查 | 完成請求 | 延遲 | 記憶體 | 轉換／收據 |
|---|---|---|---|---|---|---|---|
| `load-baseline-20260921-200844` | 1.1.0 | terminal | **PASS** | 2400／2400 | p95 66.9 ms | heap 峰 25.2 MB | 526／526 |
| `load-baseline-20260921-202729` | 1.2.0 | terminal | **PASS** | 2400／2400 | p95 50.0 ms | heap 峰 25.2 MB | 526／526 |
| `oom-retained-payloads-20260921-201516` | 1.1.0 | terminal | **FAIL** | 1415／2400 | p95 616.7 ms | heap 峰 123.6 MB | 526／526 |
| `oom-retained-payloads-20260921-202714` | 1.2.0 | terminal | **PASS** | 2400／2400 | p95 81.4 ms | heap 峰 25.8 MB | 526／526 |

- **INC-C（OOM）真的發生**：v1.1.0 注入 `retain_payloads`＋heap 上限 128 MB，460 筆 `System.OutOfMemoryException` 在 `api-stderr.txt`／`logs.jsonl`，heap 1.4→123 MB，load 在 1415／2400 中斷。
- **盲診六次全部找到根因**（`diagnosis/oom/`），A 組 Read／Grep 與 B 組 codegraph 回合相當；驗證段有不存在的檔名——見該目錄 README。
- **v1.2.0 修復後同負載 2400／2400、heap 峰 25.8 MB**；load-baseline 回歸 PASS。
- `knowledge/`：事故→根因→決策→規則（團隊 LLM wiki 格式），全部 proposed。
- 尚未跑：`slow-sync-notify`（量變大變慢）。

## 重跑

```powershell
cd examples/order-cancel-lifecycle
dotnet run --project tests/DomainTests                         # 領域規則 9 格
powershell -NoProfile -File tools/run.ps1 -scenario baseline   # 正常對照（會 build）
powershell -NoProfile -File tools/run.ps1 -scenario missing-notification -noBuild
powershell -NoProfile -File tools/run-load.ps1 -scenario load-baseline      # 壓力對照
powershell -NoProfile -File tools/run-load.ps1 -scenario oom-retained-payloads -noBuild
powershell -NoProfile -File diagnosis/oom/run-diagnosis.ps1 D4          # 盲診（消耗用量）
python tools/check.py evidence/runs/<run_id>                   # 只對帳，不啟服務
```

要看 v1.0.0 的丟失行為：`git checkout 71e57b8 -- src/Api/Program.cs VERSION` 後重跑 missing-notification。

## 明確不做／不宣稱

- 不接真金流、客戶資料、Production；`RefundRequested` 只是業務結果旗標。
- 記憶體儲存，**不保證重啟持久性**；要證明 crash recovery 才補持久化與對應測試。
- 權限用 `X-Actor` 測試身分，不是正式認證設計。
- 故障是演練注入，不是自然發生的事故；`scenarios/faults/` 在 後續 前不公開。
- 沒有基線，不宣稱開發加速或維運減載；人工分鐘欄位為 null＝未記錄。
- 診斷（後續）尚未跑；盲診用的 snapshot 須去掉 `faults/` 與 `notify_deferred` 的 `requeued` 欄位等會洩答案的內容，另行製作。

## 版本

`VERSION`＋`CHANGELOG.md`；本目錄有本機 git（未推送）。`manifest.json` 記每次 run 的 Domain／Api／scenario／faults 雜湊。
