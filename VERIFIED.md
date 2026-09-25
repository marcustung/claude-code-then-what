# 讀者視角試跑紀錄

每一筆都是在這個 repo 的乾淨副本裡，照該天 README「跑什麼」原樣執行一次的結果；找到的問題已修，修了什麼寫在備註。只加不改，最新的一筆在最下面。你自己跑出不同結果很正常（模型回覆每次不同），但「跑不跑得動」應該一樣；跑不動請開 issue 附這張表的環境與你的環境。

## 環境

- **E1**：Windows 11 Pro 10.0.26200；Windows PowerShell 5.1；Claude Code CLI 2.1.277；.NET SDK 9.0.314；Python 3.14.5；Node v24.15.0

## 紀錄

| Day | 時間 | 環境 | 指令 | 結果 | 備註（含修正） |
|---|---|---|---|---|---|
| 1 | 2026-09-20 14:12 | E1 | `git log --since="30 days ago" --format="%an" \| sort \| uniq -c \| sort -rn` | OK | 在讀者自己的 git repo 執行；本 repo 副本不是 git repo 時會報 not a git repository，屬預期 |
| 2 | 2026-09-20 14:13 | E1 | `run-day02.ps1 → check-day02.py day02-write-rerun-20260920-141330` | OK | Claude 13 s 交回 JSON；抽出 Guard.cs 後六個情境 6 passed, 0 failed。修正：原本沒有抽出／編譯步驟，新增 check-day02.py |
| 3 | 2026-09-20 14:14 | E1 | `dotnet run --project Demo.csproj` | OK | ALL TESTS PASSED（歷史程式重跑）。修正：lab README 一句『尚未發布公開 repo』已移除 |
| 4 | 2026-09-20 14:15 | E1 | `days/day04/lab: node run.cjs；lab-dotnet: dotnet run -- all；kit/review/plugin-lab: run-verify.ps1` | OK | 三段都通過；plugin 三次呼叫 93 s，V-G0-A／V-G0-B／V-S-A 的 R1–R5 全 true（V-S-A R5=true）。修正：run-verify.ps1 原本讀已搬走的 runs/G0-A、runs/S-A 提示（讀者跑會找不到檔），改讀 prompts/；輸出改為時間戳目錄；跑完自動 extract＋check；extract_result.py／check_card.py 改為接受任意路徑 |
| 5 | 2026-09-20 14:18 | E1 | `README 裡的 claude -p … --output-format json（以 fixtures/pr-A 代替讀者自己的四個檔）` | OK | 11 s、5 回合、US$0.03、is_error=false、subtype=success，四個欄位都在。修正：fixtures/pr-A 裡多一個 09-17 留下的 run-demo.json，已移出 |
| 6 | 2026-09-20 14:20 | E1 | `run-intent.ps1；run-noname.ps1` | OK | 各寫到 *-rerun-時間戳 新目錄，歷史 run 未動。intent 3 回合讀兩檔；noname 3 回合未讀 intent.md（這次它沒猜 spec.md，改要求提供路徑；結論不變）。修正：新增 tools/trace-summary.py 讓讀者一行看到工具呼叫 |
| 7 | 2026-09-20 14:21 | E1 | `run-day07-repeat.ps1；run-day07-notools.ps1；tools/trace-summary.py … --marker RULE-CONTEXT-7-KITE-0911` | OK | r2／r3 重跑：1 次 Read、標記在工具回傳與回覆、五項 [false,false,false,true,true]；notools 重跑：0 次工具呼叫、無標記、exit 0。修正：所有 runner 原本硬寫作者機器上的 claude.exe 路徑（公開版被去識別成 <HOME>，讀者跑不動），改為從 PATH 找 claude.exe／claude.cmd，找不到印安裝提示 |
| 12 | 2026-09-26 06:27 | E1 | `days/day11/lab-dev: python verify-integration.py reader-integration-02；python run-verifier-cycle.py reader-verifier-01` | OK | verify-integration：{checks:11, pass:true}。run-verifier-cycle：三段 exit 0，status=VERIFIED；report.json 的 failed_checks_before=[notification-ids-and-flags]、green_checks=11、protected_unchanged=true 與正文一致；repair.diff 只改 Program.cs 一行（false → result.RefundRequested），與正文 C# 前後對照逐字相符。三段 trace.jsonl 均有真實 tool_use（13／5／12 次），非純文字摘要。本次三段合計 123 秒／US$0.446；正文寫的是作者原始那次的 219 秒／US$0.527（見 runs/verifier-cycle-01）。時間差了近一倍，不只是計價浮動——重驗每次回合數與模型思考長度都會變，正文用「約」字已預留這個範圍，讀者重跑本就不會拿到同一個數字，只有『流程走完、發現一致』才是這篇要驗的事。 |
