# CHANGELOG

## 2.1.2（2026-10-04）
- allowed-tools 改成每條只用一個萬用字元（`Bash(python *collect.py *)`）。實測：`*x*scripts*collect.py *` 這種多個萬用字元的寫法不會命中，v2.1.1 仍三次被擋。

## 2.1.1（2026-10-04）
- allowed-tools 改用萬用字元比對腳本名稱。原因：Windows 上 `${CLAUDE_SKILL_DIR}` 展開成反斜線路徑，Claude 在 Bash 裡打正斜線，規則逐字比對失敗，marketplace 安裝後 collect.py 三次都被擋（資料夾版因命令列另給白名單而沒看出來）。

## 2.1.0（2026-10-04）
- SKILL.md 的腳本路徑由寫死的 `.claude/skills/trace-notification/scripts/` 改為 `${CLAUDE_SKILL_DIR}/scripts/`；frontmatter 加 allowed-tools 預先核准三支腳本。原因：裝成 plugin 後腳本不在 `.claude/skills/` 底下，寫死的路徑會失效。

## 2.0.2（2026-10-04）
- SKILL.md 明寫 sender_status 也只能 confirmed／unknown（complete 首跑填 notify_sent 被退回，模型改讀檢查器原始碼才修正）。

## 2.0.1（2026-10-04）
- selftest.py、gate.py 輸出改 UTF-8，修正 Windows cp950 主控台崩潰。

## 2.0.0（2026-10-04）
- 新增結果契約 v1 與固定檢查（Day 19 check_result.py，原封不動）。
- collect.py 增加 records；接收紀錄的版本沿用同一通知的 notify_sent，並標 version_source。
- 新增 gate.py（接頭）與 selftest.py。

## 1.0.0（Day 17）
- 查核迴圈與簡易 JSON 輸出。
