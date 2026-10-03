# 交接實跑發現

## F1 selftest 在 cp950 主控台崩潰（2026-10-03 作者機）
- 現象：`python selftest.py` → UnicodeEncodeError: cp950 cannot encode U+2265（≥）。
- 原因：Windows 中文主控台預設 cp950；腳本輸出含非 Big5 字元。gate.py 輸出中文 JSON 同樣有風險。
- 修正：selftest.py、gate.py 開頭將 stdout/stderr 設為 UTF-8（errors=replace）。v2.0.1。

## F2 Skill 沒寫清楚 sender_status 允許值（complete-20261003-043626）
- 現象：Claude 填 sender_status="notify_sent"（Day 17 用語），gate 退回；之後 grep／sed 讀 check_result.py 查允許值，改成 confirmed 後通過。
- 意義：文件缺一句，接手者（模型）就去讀評分程式。這次修正方向正確，但「從檢查器反推答案」本身要被看見；外層重跑 gate 仍是唯一可信判定。
- 修正：SKILL v2.0.2 明寫兩個狀態都只能 confirmed／unknown。

## F3 Bash 白名單不等於只能跑白名單（同一次）
- 允許清單只列 gate.py／collect.py／selftest.py，但 cat、ls、grep、sed 等唯讀指令仍執行；只有含 heredoc 寫檔、含 $? 變數的兩次被拒。
- 意義：INSTALL.md 的「Bash 只執行 gate.py」寫法過度承諾。改寫為「寫入只限 Write(out/**)；唯讀指令 Claude Code 預設可執行」。

## F4 沒有執行權限時，誠實但多慮（no-bash-20261003-043826）
- Claude 明說「固定檢查未執行，不能說已通過」，結果停在交人核對；外層補跑 gate 判 READY_FOR_REVIEW，它手推的 evidence_refs 是對的。
- 它擔心 task.json 沒有 notification_id 會讓 gate 失敗；實際上 gate 會從工具收集的發送紀錄取 ID。文件沒寫，接手者只能猜。INSTALL.md 補一句。

## F5 只交 SKILL.md（skill-only-20261003-043901）
- Claude 找不到 scripts/，明說兩支腳本不存在，兩個狀態都保守標 unknown、evidence_refs 留空，沒有自行補寫腳本。
- 意義：只交 Skill 文件，方法無法完成；SKILL.md 寫了步驟，但步驟依賴的零件不在。

## 四情境總表
| 情境 | Skill | 回合 | 秒 | US$ | 外層 gate | Claude 自述 |
|---|---|---|---|---|---|---|
| complete | v2.0.1 | 14 | 36.7 | 0.158 | READY_FOR_REVIEW | 退回一次，讀檢查器後修正 |
| missing | v2.0.2 | 10 | 34.5 | 0.135 | NEEDS_FOLLOWUP | 列缺 receipts.json 與下一步 |
| no-bash | v2.0.2 | 12 | 34.6 | 0.141 | READY_FOR_REVIEW | 固定檢查未執行，不稱通過 |
| skill-only | v2.0.2 | 8 | 42.0 | 0.098 | 無法執行（無 gate.py） | 腳本不存在，待查 |

模型 claude-sonnet-5-5；同一台作者機，乾淨目錄＋--setting-sources project（不讀作者使用者設定），不是另一台機器或另一個真人。

## 補充：團隊 marketplace 交接（2026-10-04，v2.1.0–v2.1.2）

把方法包包成 plugin，放進本機 marketplace（`d20-team`），在乾淨目錄用 `--scope project` 加入並安裝（寫進該目錄的 `.claude/settings.json`；全域的 `~/.claude/plugins/installed_plugins.json`、`known_marketplaces.json` 也會留下登記，`~/.claude/settings.json` 不變）。命令列**不給** Bash 白名單，模擬接手者手上只有包本身。

| 次 | 版本 | 權限來源 | 回合／秒／US$ | 腳本被擋 | 外層檢查 |
|---|---|---|---|---|---|
| marketplace-232222 | 2.1.0 | SKILL.md `allowed-tools`（`${CLAUDE_SKILL_DIR}`） | 13／44.5／0.141 | 3 | NEEDS_FOLLOWUP |
| marketplace-232352 | 2.1.1 | 同上，改多個萬用字元 | 11／35.5／0.081 | 3 | NEEDS_FOLLOWUP |
| marketplace-232533 | 2.1.2 | 同上，改單一萬用字元 | 14／35.4／0.126 | 3 | NEEDS_FOLLOWUP |
| folder-skillperm-232630 | 2.1.2 | 對照：資料夾版，只靠 SKILL.md | 14／39.9／0.138 | 3 | NEEDS_FOLLOWUP |
| marketplace-team-232727 | 2.1.2 | 專案 `.claude/settings.json` 的 permissions.allow | 15／32.9／0.134 | 3 | NEEDS_FOLLOWUP |

確認的事：
1. marketplace 加入、安裝、載入都成功；Skill 以 `trace-notification:trace-notification` 被呼叫；自測通過；外層檢查通過契約。
2. **路徑寫死會壞**：v2.0.2 的 SKILL.md 寫死 `.claude/skills/...`，裝成 plugin 後腳本不在那裡；改用 `${CLAUDE_SKILL_DIR}`（v2.1.0）後 Claude 找得到腳本。
3. **權限沒有跟著包過去**：五次都由 Claude 自己去跑 collect.py，三次都被擋。SKILL.md 的 allowed-tools（資料夾版、plugin 版都一樣）和專案設定的 allow 規則，在這次的非互動（`-p`）執行裡都沒有生效。原本四個情境能跑，是因為命令列另給了白名單。
4. 五次 Claude 都沒有假裝通過：照實列 collect.py／gate.py 為缺件，兩個狀態填 unknown，外層判 NEEDS_FOLLOWUP。
5. 小測試（Haiku，命令列白名單）：`Bash(python *collect.py *)` 命中；`Bash(python *x*scripts*collect.py *)` 不命中。

未確認：專案設定的 allow 規則為何沒生效（推測與新目錄尚未被信任有關，未驗證）；互動模式下接手者會被詢問一次、核准即可跑，這次未驗證。
