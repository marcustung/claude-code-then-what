# Day 23：通知送出了，接收端卻沒收到

本機 .NET 教學服務（訂單取消＋通知），故障為刻意注入，非公司線上事故。

| 目錄 | 內容 |
|---|---|
| `v1.0.0/src` | 修正前程式（Git revision `71e57b8`）：延後分支先把 `notify_sent_total` 加一再 `continue` |
| `v1.1.0/src` | 修正後程式（`fe980e5`）：延後改為重新排隊，`sent` 只在接收端成功回應後增加 |
| `runs/` | 四次結果：正常對照、故障 v1.0.0、故障 v1.1.0、正常回歸，各含 requests、logs、metrics、receipts、manifest、check.json |
| `tools/check.py` | 固定對帳程式（v1.1.0 版），不由模型判定 |
| `specs/notification-contract-v2.1.md` | 通知契約（新增提案，不是歷史修復當時已存在的文件） |
| `claude-run/` | 2026-10-07 Claude 唯讀對照 3 次（Sonnet，只開 Read／Grep／Glob）：提示、去洩漏步驟、工作目錄與完整輸出；見其中 README |

## 自己重算

`check.py` 會寫出 `check.json`，先複製再執行：

```powershell
$run = "runs/missing-notification-20260921-193704"
$copy = Join-Path ([IO.Path]::GetTempPath()) ("day23-" + [guid]::NewGuid())
Copy-Item -LiteralPath $run -Destination $copy -Recurse
python tools/check.py $copy
```

預期 `FAIL`：接收端 3、成功轉換 9、sent_total 9。換成 `runs/missing-notification-20260921-193835` 預期 `PASS`，並顯示延後重排 45 次。

## 界線

同一組故障、每版各跑一次；尚未驗持續超載、重啟恢復，也沒有補送原先遺失的六筆。Claude 實跑為同一份資料 3 次，不估一般準確率。
