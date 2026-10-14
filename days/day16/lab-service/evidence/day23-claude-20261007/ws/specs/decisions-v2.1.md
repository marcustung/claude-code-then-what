# 決策紀錄 v2.1

| 日期 | 項目 | 決定 | 誰 | 狀態 |
|---|---|---|---|---|
| 2026-09-21 | 通知契約 NC-01～07 | 起草；等作者接受 | Claude Code 起草 | **proposed** |
| 2026-09-21 | 重複取消的 API 回應 | 200 `{ok:true, transitioned:false}`（冪等成功）而非 409；理由：呼叫端重送不應被當錯誤，但 `transitioned=false` 讓對帳能區分 | Claude Code 提案 | proposed |
| 2026-09-21 | 已出貨取消 | 409 `{ok:false, reason:"shipped"}`；不通知 | 沿 v2 BR-02 | 沿用 |
| 2026-09-21 | 重試上限 | 3 次、退避 200／400／800 ms；超過進 dead_letter | Claude Code 提案 | proposed |
| 2026-09-21 | 儲存 | 程序內記憶體＋JSONL 證據；不保證重啟 | Claude Code 提案 | proposed |

作者接受後：改狀態、填日期，並在 `CHANGELOG.md` 對應版本記一行。
