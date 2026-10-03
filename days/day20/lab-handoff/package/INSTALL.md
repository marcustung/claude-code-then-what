# 安裝 trace-notification v2.1.2

## 包裡帶走的 vs 你要自己設定的

| 包裡帶走（共同方法） | 你要自己設定（使用端環境） |
|---|---|
| `SKILL.md`：查核步驟、結果契約、檢查沒過怎麼辦 | 案例資料的位置（`task.json`、`data/`） |
| `scripts/`：收集、接頭、固定檢查、自測 | Log server 的查詢工具、服務位址、帳號與權限 |
| `VERSION`、`CHANGELOG.md` | 允許執行這三支腳本的權限（見下方） |

作者的帳號、服務位址不在包裡，也不該在包裡。

## 前提
- Python 3.8 以上（只用標準函式庫）
- Claude Code CLI，已登入

## 方式 A：放進 repo（同一個 repo 的團隊）
1. 把整個 `.claude/skills/trace-notification/` 放到專案根目錄並 commit。**不要只放 SKILL.md**，腳本要一起帶。
2. 自測：`python .claude/skills/trace-notification/scripts/selftest.py`，看到 `7/7 PASS` 才算裝好。

## 方式 B：團隊 marketplace（跨 repo、整個部門）
1. 維護者把方法包放進團隊的 marketplace repo（`plugins/trace-notification/`，含 `.claude-plugin/plugin.json`）。
2. 接手者在自己的專案根目錄：
   ```text
   claude plugin marketplace add <團隊 marketplace repo> --scope project
   claude plugin install trace-notification@<marketplace 名稱> --scope project
   ```
   `--scope project` 只寫進該專案的 `.claude/settings.json`；本機的 plugin 清單（`~/.claude/plugins/`）仍會留下登記。
3. 也可以直接 commit 一份 `.claude/settings.json`（範本見 `settings.template.json`），同事 clone 後在 Claude Code 裡同意安裝即可。
4. 自測：腳本在 Skill 的目錄底下，`SKILL.md` 用 `${CLAUDE_SKILL_DIR}` 指向它，不必知道實際路徑；要手動跑時用 `claude plugin details trace-notification` 找安裝位置。

## 權限（請先讀）
| 工具 | 用途 | 沒有會怎樣 |
|---|---|---|
| Read／Grep／Glob／Skill | 讀 Skill、資料、程式 | 無法查核 |
| Write（只寫 `out/`） | 寫 `out/result.json` | 結果無法交給檢查器 |
| Bash：`collect.py`、`gate.py`、`selftest.py` | 收集來源、跑固定檢查 | 停在「固定檢查未執行」，結果待查 |

**權限不會跟著包過去。**2026-10-04 實測（非互動 `-p`，Windows）：`SKILL.md` 的 `allowed-tools`、專案 `.claude/settings.json` 的 allow 規則都沒有生效，三支腳本被擋；只有命令列 `--allowedTools` 生效。所以：
- 互動使用：第一次執行時 Claude Code 會詢問，**請核准這三支腳本**。
- 排程或非互動使用：在命令列給 `--allowedTools "Bash(python *collect.py *),Bash(python *gate.py *),Bash(python *selftest.py *)"`。每條規則只用一個萬用字元，`*x*y*` 這種寫法實測不會命中。
- 唯讀指令（cat、grep 等）依 Claude Code 預設仍可執行；真正限住寫入的是 `Write(out/**)`。

## 失敗去向
| 狀態 | 意思 | 誰接 |
|---|---|---|
| READY_FOR_REVIEW | 條件齊，交人核對 | 服務 Owner |
| NEEDS_FOLLOWUP | 接收端 unknown，列了缺件 | 查核者補查 |
| RETURN_FOR_EVIDENCE | 缺依據或不一致 | 查核者修正後重跑 |
| INPUT_ERROR | 結果檔不存在或通知 ID 不唯一 | 操作者檢查輸入 |

通過檢查不等於可以補送或結案：`approved` 固定為 false。

## 停止使用的條件
- 自測任何一項 FAIL。
- 資料格式改變（例如 receipts 開始帶版本欄位）：先更新 collect.py 與自測，再使用。
