# ORD-142 v2｜一張票走完（Day 16 lab）

Day 6 的教學示範訂單取消（`spec-v1.md`、`decisions-v1.md`）開 v2：改一條規則（BR-03 退款要求）、補一條待確認（BR-04 再次取消）。作者本人在互動模式下走十步，全程留 session 檔、git log、PR。腳本見 `SESSION-SCRIPT.md`。

- `ticket/ORD-142-v2/02-RULES.md`：這張票唯一的規則來源（BR-01–04、SC-01–07）
- `src/Cancellation.cs`、`tests/Program.cs`、`Demo.csproj`：v1 程式（與 Day 6 impl 同檔）
- `CLAUDE.md`（含 RULES-TOKEN）、`.claude/settings.json`（freeze-guard hook）、`.claude/agents/reviewer.md`（唯讀 reviewer）
- 十站遺產怎麼用在這裡：Day 6 spec 模板→02-RULES；Day 7 規則進 context→CLAUDE.md；Day 8 引用附行號→CLAUDE.md 回報規則；Day 9 不堆規則→CLAUDE.md 只有 12 行；Day 10 先紅再綠→做法；Day 11 reviewer 唯讀→agents/reviewer.md；Day 12 hook→settings.json＋freeze.json；Day 13 哨兵→RULES-TOKEN；Day 14 三層紀錄→session 檔＋git log；Day 15 回讀→PR 合併後 `dotnet run`
