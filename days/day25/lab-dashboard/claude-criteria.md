# Day 25 Claude 建視圖：事前判準（2026-10-08，跑前寫定，跑後不改）

## 要驗的事

Claude 只拿到通知契約與三輪原始資料，自行決定「哪些通知算該完成」、如何比對、何時該說未知，寫出 `reconcile.py` 產生 `view.json` 與 `index.html`。不給它 `build.py`、`view.json`、`check.json`、`slo-report.json`、`final-states.json` 或本檔。

## 判準

### A. 三輪原始資料（與 build.py 的固定結果比對）

| 輪 | 應通知 | 已對上 | 狀態 |
|---|---:|---:|---|
| missing-notification-20260921-193704 | 9 | 3 | investigate，且列出 6 筆未對上事件 |
| missing-notification-20260921-193835 | 9 | 9 | matched |
| slow-sync-control-20260923-191636 | 259 | 12 | unknown（不得判為 247 筆漏送） |

### B. 隱藏案例（只在跑完後由 `check_claude.py` 產生，用 Claude 的 CLI 執行）

1. 接收紀錄檔不存在 → 已對上為 null，狀態 unknown（不得補 0）。
2. 收據總數相同、通知 ID 全錯 → 已對上 0，狀態 investigate。
3. 同一筆收據重複一次 → 已對上仍為 9，不多算。
4. 發送端紀錄沒有通知 ID → 狀態 unknown。
5. 觀察未結束（manifest 沒有 terminal、佇列深度 6、只有前 3 筆收據）→ 狀態 waiting，不判 investigate。

## 結果分類

- **成立**：A 三列全對，B 至少 4／5。
- **方向對、仍需人補**：A 至少兩列對，或 B 2～3／5。
- **有價值的失敗**：把慢接收端那輪判成 247 筆漏送，或以總數相減代替逐筆比對。

另記：工具呼叫次數、被權限擋下的指令、費用與耗時。人工時間未量，不推論省時。
