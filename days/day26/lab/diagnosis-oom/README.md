# INC-C 盲診｜壓力測試中 OOM：Claude 能不能從紀錄找到根因

2026-09-21。診斷者只看 `snapshot/`：事故摘要、原始紀錄（logs／metrics 時間線／requests／stderr／對帳輸出）、**事故當時的原始碼變體**（把演練注入寫成開發者會寫的樣子：`RequestAudit.Keep(...)` 常開、無旗標；`faults` 機制與「注入」字樣全部移除）、規格。故障答案（`scenarios/faults/`）與 run 名稱都不在快照裡；快照內的 run_id／request_id 已改為 `INC-C-*`。

`--model sonnet --effort low`、`--setting-sources ""`。A 組 Read／Grep／Glob 三次；B 組另掛 codegraph MCP（`codegraph init snapshot`）三次。六次輸出全部保留，不挑。

| run | 組 | 回合 | 工具呼叫 | 秒 | USD | 第一假設指到 RequestAudit | 引用檔案行號存在 | 修法位置 | how_to_verify 引用了不存在的檔 |
|---|---|---|---|---|---|---|---|---|---|
| D1 | A | 10 | 9 | 58.0 | 0.229 | 是 | 7/7 | `src/Api/Program.cs:146` | tools/load.py, scenarios/oom-retained-payloads.json, tools/check-load.py |
| D2 | A | 9 | 8 | 45.2 | 0.195 | 是 | 7/7 | `src/Api/Program.cs:52` | tools/run-load.ps1, tools/check-load.py |
| D3 | A | 9 | 8 | 42.0 | 0.173 | 是 | 4/4 | `src/Api/Program.cs:52` | scenarios/load-baseline.json, tools/run-load.ps1, tools/load.py, check.json |
| M1 | B | 9 | 8 | 45.2 | 0.257 | 是 | 6/6 | `src/Api/Program.cs:52` | tools/load.py, tools/check-load.py, check.json |
| M2 | B | 9 | 8 | 57.4 | 0.203 | 是 | 7/7 | `src/Api/Program.cs:146` | scenarios/oom-retained-payloads.json, check.json |
| M3 | B | 10 | 9 | 64.8 | 0.255 | 是 | 7/7 | `src/Api/Program.cs:149` | tools/load.py, scenarios/oom-retained-payloads.json, tools/check-load.py, check.json |

## 看到什麼

1. **六次都找到根因**：`RequestAudit` 的 static List 無上限保留每筆 64 KB payload；機制講對（32 併發 × 64 KB × 2400 筆 → 撐到 128 MB 上限 → `OutOfMemoryException`）；引用的檔案與行號全部存在。都排除了 OrderStore、JsonlLog、GC 設定；有幾次把「Unbounded Channel 佇列堆積」列為第二假設（medium），合理。
2. **索引沒有讓它更快**：B 組回合 9–10、費用 0.20–0.26，與 A 組 9–10、0.17–0.23 相當；快照只有 2 個 C# 檔，Read 一次就讀完，索引無用武之地——與 Day 11 的觀察一致。
3. **診斷對，驗證段卻引用了不存在的檔案**：六次的 `how_to_verify` 都提到 `tools/load.py`、`tools/check-load.py`、`scenarios/oom-retained-payloads.json` 等——**快照裡沒有這些檔**（grep 為零）。這些是模型從 `check.json` 的欄位、工作目錄名 `diagnosis/oom/` 與自己的結論拼出來的合理路徑。提示要求「沒證據寫未確認」，它在根因段做到了，在驗證段沒有。Day 8 的教訓在這裡又出現一次：核對要做到最後一段。
4. D1 還抓到快照本身的瑕疵：`RequestAudit.Keep(id, rid, payload)` 在 `rid` 宣告之前——這是做快照變體時的順序錯誤（真實程式沒有），它標為「未確認」而沒有掩蓋。

## 修復與驗證

依六次一致的修法（有上限的緩衝、不存完整 payload）做 v1.2.0：`Retained` 改環狀緩衝 256 筆、每筆留前 256 字＋原長度。同一注入、同一負載重跑：**2400／2400 完成、p95 81 ms、heap 峰 25.8 MB（修前 123.6 MB）、無 OOM**；load-baseline 回歸 PASS。修復由 AI 實作；作者尚未接受（`specs/decisions-v2.1.md`）。

## 不能說的

一個模型、六次、一個故障；快照是為演練做的變體，不是自然事故；「找到根因」在這裡容易——兩個檔、一個明顯的 static List——真實系統不會這麼乾淨。

## 檔案

`prompt.txt`、`run-diagnosis.ps1`、`summarize.py`、`summary.json`、`snapshot/`（含 `.codegraph/`）、`runs/D1–D3、M1–M3/`（trace、meta、B 組另有 mcp.json）。
