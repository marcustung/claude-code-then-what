# Day 6 spec-first 實跑（2026-09-18）

兩次 `claude -p`（sonnet alias、low effort、`--strict-mcp-config --no-session-persistence --setting-sources ""`），腳本 `run.ps1`，每個子目錄有 prompt.txt、trace.jsonl、meta.json、result.md（模型最終回覆）。

| 子目錄 | 輸入 | 工具 | 回合／時間／費用 | 結果 |
|---|---|---|---|---|
| `draft/` | spec.md（Day 3 一句需求＋骨架＋限制） | Read／Grep／Glob | 4／38,900 ms／US$0.0599 | 驗收草稿：一條明示行為、五個待確認問題、受阻範圍 |
| `diagram/` | spec.md | Read | 2／12,550 ms／US$0.0380 | 一條有來源的邊＋三條待確認；多畫 Placed→Shipped、待確認放 note |
| `intent/` | intent.md（待確認草稿）＋spec.md | Read | 3／15,454 ms／US$0.0392 | 讀兩檔；指出 spec 已把 RefundRequested 寫進簽名、intent 尚未決定；三題待確認；未列來源版本 |
| `impl/` | spec.md、decisions.md（DEMO-DECISION-01：三條已確認、一條待確認）、只有簽名的 Cancellation.cs、空 Program.cs | Read／Grep／Glob／Write／Edit／Bash | 12／56,763 ms／US$0.1536 | 實作三條並各寫一測試；`dotnet run` 三項 PASS、exit 0；重複取消未寫測試、註解標未驗證；未加 null 檢查 |

界線：合成教學案例；DEMO-DECISION-01 是假設決策，不是真實 Owner 確認；各一次執行，不是統計；`impl/` 由模型寫檔並執行 dotnet，作者 09-18 重跑 `dotnet run --project Demo.csproj` 結果相同。

## 09-19 補充兩筆

| 子目錄 | 做什麼 | 結果 |
|---|---|---|
| `noname/` | 同目錄放 intent.md 與 spec.md，提示**不指名檔案**只說「整理驗收草稿」，只開 Read（5 回合、24,417 ms、US$0.0309） | 它 Read 資料夾路徑（EISDIR 失敗）、Read README.md（不存在）、同時 Read spec.md 與 SPEC.md（大小寫不敏感，同一檔）後照做；**intent.md 一次都沒讀**，草稿沒有目的段。第一次執行因 PowerShell stdin 為 Big5 而送成亂碼，模型回「訊息似乎是亂碼」（該次 trace 未保留，僅記結果）；改設 `[Console]::InputEncoding` 為 UTF-8 後重跑 |
| `impl-check/` | 複製 impl 的 Cancellation.cs，另寫觀察用 Program.cs，輸入已取消、未出貨的訂單 | `OUTPUT Cancelled=True RefundRequested=False threw=false`，證實文章「重複取消仍會走完函式」是執行結果，不只是讀程式 |

stdin 編碼：09-19 前的四次（draft、impl、diagram、intent）輸出逐項對應提示的結構，判定提示完整到達；之後的 runner 一律設 UTF-8。
