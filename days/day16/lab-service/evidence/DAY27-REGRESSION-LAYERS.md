# Day 27：測試全綠，OOM 回來了（2026-10-03）

把 v1.2.0 已修好的 OOM 改回去（`scenarios/faults/regress-oom.json`：`retain_payloads`＋`regress_unbounded_retain`，重現 v1.1.0 修復前的無上限保留），三層既有品質關卡各跑一次。不呼叫模型。

| 關卡 | 指令 | 回歸開關打開 | 對照（修好的版本） |
|---|---|---|---|
| 領域測試 | `dotnet run --project tests/DomainTests` | **PASS**（全部條件通過） | — |
| 端到端功能檢查 | `tools/run.ps1 -scenario regress-oom-functional` | **PASS**：10 項全過，含收據 == 成功轉換 == 9、sent == 收據 | — |
| 壓測檢查 | `tools/run-load.ps1 -scenario regress-oom-load` | **FAIL**：`System.OutOfMemoryException`；完成 1,069／2,400；32 筆無回應；p95 379 ms（門檻 250）；heap 1.4 → 123.3 MB（門檻 +64 MB）；崩潰前成功轉換 526、收據只有 202 | `oom-retained-payloads`：**PASS**，p95 31 ms，heap 1.4 → 24.8 MB，收據 526／526 |

原件：`evidence/runs/regress-oom-functional-20261003-141440/`、`evidence/runs/regress-oom-load-20261003-141449/`、`evidence/runs/oom-retained-payloads-20261003-141507/`。

## 讀法

1. 領域測試與功能檢查**看不到**記憶體回歸：功能情境只有 12 張訂單、沒有大 payload，保留多少都不會撐爆。
2. 只有接近真實負載（2,400 筆、每筆 64 KB、heap 上限 128 MB）才現形。
3. 崩潰前通知對帳也已經壞了（成功轉換 526、收據 202），但功能檢查的小樣本不會觸發。

## 限制

heap 上限 128 MB 是演練用的縮小環境；回歸開關為演練用（預設關閉），重現已修 bug 被改回去，不是自然事故；各跑一次。
