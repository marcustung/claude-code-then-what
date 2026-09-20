# Day 7、9、10｜Claude 新實驗證據包

初始設計 2026-09-11；成功 Claude runs 為 UTC 2026-09-11 23:19 起，即台北 2026-09-12。公開合成任務的新實驗，非公司歷史交付或效率成果。

## 已取得結果

- Day 2（2026-09-12 補跑，`day02-write/`）：只給 ticket 一句需求與空骨架，要求回傳程式、最小測試、說明與「ticket 未寫的假設」。Claude 回傳 `rejected && !(reopenRequested && authorized)` 版本、六個測試、六條假設（第一條明寫例外路徑是由「直接」一字推出）。本機 `dotnet run` 六案全過 exit 0；`hashes.txt` 記錄回傳 source 與被編譯檔案相同。一回合，無工具，`claude-sonnet-5`。此為 Day 2 結尾與 Day 3 開場的實跑材料。
- Day 7：Read 工具讀取卡片成功；回傳 marker、RULE-01；五項情境全對，理由與未知符合卡片。顯式讀檔，不是自動載入驗證。2026-09-19 同輸入重跑兩次（`day07-r2/`、`day07-r3/`，CLI 2.1.277，`run-day07-repeat.ps1`），皆 2 回合、一筆 Read、15/15。2026-09-19 負對照 `day07-notools-1/`、`-2/`（`run-day07-notools.ps1`，同卡同指令、`--tools ""`）：1 回合、無工具呼叫、無標記、無 JSON，回覆為偽裝的工具呼叫文字；exit 0。
- 成功 run 回報模型 ID `claude-sonnet-5`，CLI 版本 2.1.269，使用 `sonnet` alias 與 low effort。模型名稱依本機 trace 原樣報告，不作外部產品版本推論。

## 檔案與重跑

- `protocol.md`：預先規格；`run.ps1`：實際 runner。
- `day02-write/`：prompt、trace、回覆、`answer.json`、`Guard.cs`、`Program.cs`、`check/`（csproj 與 `run.txt`）、`hashes.txt`；runner 為 `run-day02.ps1`。
- `day07/`：prompt、卡片、trace、回覆與 metadata。
- `inspect.ps1`、`results.json`：解析及機械計數；文字解釋查核另見文章。
- `day07-sandbox-failed/`：首次 API ConnectionRefused，usage 為零；不納入模型效果分數。
- `checks.txt`：證據鏈核對；`manifest.json`：來源與輸出 SHA-256。

重跑修正版（不呼叫 Claude）：

```powershell
```

重新解析既有輸出（不呼叫模型）：

```powershell
powershell -NoProfile -File inspect.ps1
```

重新取得模型輸出時，先將 run.ps1、rule-card.md 複製到新的實驗目錄，保留本轮證據。runner 使用已登入的 Claude CLI，會使用相應用量，不是離線回放，不保證輸出可重現。

## 限制

同一題五情境重複三次，不是十五件獨立任務；沒有顯著性或等效檢定。A/B 規則使用簡短自然語言，部分輸出疑問提示條件仍可更明確。本輪未事後改 Prompt 取代結果。


原始 trace 含本機路徑、session ID 與用量；公開文章採正文節錄。沒有公司金額、客戶資料或商業 source。
