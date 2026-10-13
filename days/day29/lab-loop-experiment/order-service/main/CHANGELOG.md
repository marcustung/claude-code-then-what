# CHANGELOG

## 未發版：Day 16 開發實跑（commit `508bd3f`，2026-09-21）
- **版號維持 1.2.0，未 bump。** 該次實跑由 `885e521` 刻意把 Domain 退回 Day 6 的 v1，再由 Claude Code（AI）走七步（plan→tests→impl→trap→review→reviewdirect→pr）重新推導 v2。結果與 1.2.0 的實作**行為完全相同**：分支順序（BR-02→BR-04→BR-01/BR-03）與運算式（`RefundRequested: order.Paid`）逐一相符，差異只有大括號、空行與註解措辭；`src/Api/Program.cs` diff 0 行。**沒有功能變更，故不升版。**
- 因格式與註解不同，`src/Domain/Cancellation.cs` 的 SHA256 由 `f8cd1d0f…` 變為 `722b3b5c…`。證據 `manifest.json` 以 `domain_sha256` 定位程式，**雜湊改變不等於行為改變**，比對時須併看本節。
- 2026-09-23 於此程式補跑 `baseline`（PASS，十項對帳全過）與 `missing-notification`（PASS，`notify_deferred` 重排 45 次未丟失），確認 1.1.0 的重排修法與 1.2.0 的有界緩衝在此之後仍成立。
- `PR.md` 追溯表由 AI 依原件產生、行號可對回，**Owner 尚未接受任何一列**；proposed 維持 proposed。

## 1.2.0（2026-09-21）
- 修復 INC-C（OOM）：客服查詢暫存 `Retained` 由無上限 List 改為環狀緩衝（256 筆、每筆保留前 256 字＋原長度）。修法依六次盲診（D1–D3、M1–M3）一致指向的根因；由 Claude Code（AI）實作，作者接受與否記於 `specs/decisions-v2.1.md`。
- 新增：`tools/run-load.ps1`（壓力情境：崩潰捕捉、metrics 時間線、port 守衛）、`tools/load.py`、`tools/check-load.py`；`/metrics` 加 latency 直方圖、GC heap、working set、gen2 次數；例外中介層把未處理例外寫進 `logs.jsonl` 與 stderr。
- 演練注入新增 `retain_payloads`、`sync_notify`；接收端加 `OC_SINK_DELAY_MS`。

## 1.1.0（2026-09-21）
- 修復：通知 worker 在佇列壓力下（`notify_drop_over_queue` 命中）不再「延後不重送、sent 照加」。延後改為重排到隊尾（最多 5 次）並另計 `oc_notify_deferred_total`；`oc_notify_sent_total` 只在接收端回 2xx 後才加（NC-04、NC-05）。
- 故障注入檔不變；同一注入下對帳應通過。修復由 Claude Code（AI）依對帳結果提出並實作；作者接受與否記於 `specs/decisions-v2.1.md`。
- 未變：儲存仍為程序內記憶體；`RefundRequested` 仍只是業務結果。

## 1.0.0（2026-09-21）
- Domain：沿 Day 6 v1 規則＋Day 16 v2 規格（BR-01–04）；`RefundRequested` 為業務結果旗標。
- 新增：薄 HTTP API、通知 worker、本機 fake sink（獨立收據）、scenario runner、對帳 checker。
- 通知契約 v2.1 為**提案**，未經作者接受。
- 已知：故障注入 `notify_drop_over_queue` 可用（演練用）；未修復版本會讓 `notify_sent_total` 與收據不符。
