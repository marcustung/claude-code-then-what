# kit/review：AI 寫的程式，人要怎麼審（Day 3 落地包）

對應文章：Day 3〈AI 寫程式很快，但為什麼我還是不敢 Approve〉。案例原件在 `labs/day03-order-cancel/`（一次 Claude CLI 呼叫、七組情境十八個斷言、原樣 source 與回覆）。

這個目錄是「三層檢查」在 GitHub 上能直接裝的部分。它是工作設計，不是已證明能降低審查工時的制度；裝了之後要用退回率、revert、事故回頭校準（見文末）。

## 內容

| 檔案 | 用途 | 裝到哪 |
|---|---|---|
| `PULL_REQUEST_TEMPLATE.md` | 五項交接契約：可追溯、獨立證據、語意邊界、影響範圍、可解釋 | `.github/PULL_REQUEST_TEMPLATE.md` |
| `CODEOWNERS.example` | 核心規則所在路徑指定 Owner；路徑只是線索，要配合保護規則才擋得住 | `.github/CODEOWNERS` |
| `branch-protection-checklist.md` | 讓 Owner 審查與必要檢查真的成為合併條件的設定清單，含繞過權限核對 | 設定 repo 時照表勾 |
| `routing-policy.yml` | 判級規則：確定性閘門先跑，AI 只當第二意見，不明就升級 | CI 或 Danger／reviewdog 讀取 |
| `review-deep-dive-checklist.md` | 進到第三層以後，人要深挖的八件事，每件附訂單取消案例的問法 | Reviewer 手邊 |
| `rejection-note-example.md` | 退件單範例：缺哪個依據、誰補、補完怎麼判 | 退件時複製 |
| `claude-review.yml` | Claude Code GitHub Action 當第二位 Reviewer：只准評論、發現必附來源、觸及核心規則自動標 owner-required | `.github/workflows/claude-review.yml` |
| `diagrams/*.mmd` | 狀態圖、循序圖、判級流程圖的 mermaid 原始碼 | 交接物附圖用 |

## 三層各自用什麼工具（選項，不是推薦名單）

| 層 | 做什麼 | 常見工具 |
|---|---|---|
| 第一層 工具 | 編譯、格式、既有測試、靜態與安全規則；失敗就退，不准模型解釋掉 | CI（GitHub Actions）、linters／formatters、單元測試、Semgrep／CodeQL、依賴掃描 |
| 判級 | 路徑、Owner、diff 大小、敏感關鍵字（金額、授權、狀態轉換、資料遷移） | CODEOWNERS＋branch protection、Danger／reviewdog 讀 `routing-policy.yml`、PR labels |
| 第二層 AI 對照材料 | 給規格版本、呼叫端、測試，要求發現附來源；找不到寫不知道；保存誤報 | Claude Code `/review`（GitHub Action）、GitHub Copilot code review、CodeRabbit 等；輸出進 PR comment，不自動核准 |
| 第三層 Owner | 核心規則、例外、接受條件；附前後狀態圖／循序圖 | 人；退件單格式固定 |
| 校準 | 每季看退回率、revert、事故、AI 意見採納率與誤報率，回頭改閘門 | 你的 issue tracker 與 git 紀錄|

## 第一週怎麼開始（三步）

1. 放 PR 範本與 CODEOWNERS，開 branch protection：必要審查 1 人、必要檢查＝現有 CI、關掉管理員繞過。半天。
2. 在 `routing-policy.yml` 填三條路徑規則（付款、授權、狀態機）與一條 diff 大小規則；先用 label 手動標，不急著自動化。半天。
3. 選一個 AI reviewer 當第二位 Reviewer，只准評論不准核准；一個月後統計「有用／誤報／被處理」三個數。

## 業界對照（只引用，不代表本包已達同等效果）

- DORA 2025：AI 讓個人產出上升，Review 管線沒等比加速時，未審 PR 排隊吃掉組織層的增益。
- Uber uReview：首次審查時間 2024 年 3 小時到 2026 年 9 小時；AI 當第二位 Reviewer，產生→過濾→驗證→去重。
- Meta RADAR：確定性閘門→靜態規則→風險分數→LLM→確定性規則，只自動落地低風險 diff；成效看 revert 率與事故率。
- Google Tricorder／Critique：靜態分析結果自動進 review 工具，附一鍵修正。

來源見文章資料說明。

## 對應的開源專案（2026-09 查證；選項不是背書）

| 用途 | 開源專案 | 授權／型態 | 放在哪一層 |
|---|---|---|---|
| PR 政策即程式碼（diff 大小、路徑、必附欄位、缺 label 就 fail） | [danger/danger-js](https://github.com/danger/danger-js)（另有 Ruby／Swift／Kotlin／Python 版） | MIT | 判級閘門 |
| 把 linter／SAST 結果貼回 PR 變更行、過濾噪音 | [reviewdog/reviewdog](https://github.com/reviewdog/reviewdog) | MIT | 第一層輸出進 PR |
| 靜態與安全規則（可自寫規則對「Paid→Refund」這種樣式） | [semgrep/semgrep](https://github.com/semgrep/semgrep)、[github/codeql](https://github.com/github/codeql) | LGPL／MIT（CodeQL 引擎有使用條款） | 第一層 |
| 開源 AI Reviewer，可自架、自選模型，/review /describe /improve | [qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent) | MIT（雲端版另計） | 第二層 |
| Claude 當 Reviewer 的官方 Action；另有安全審查專用 Action | [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action)、[anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) | MIT | 第二層 |
| 政策引擎（判級規則寫成 Rego，CI 裡判） | [open-policy-agent/conftest](https://github.com/open-policy-agent/conftest) | Apache-2.0 | 判級閘門（進階） |
| 自架 code review 系統（Google 系血統，必要審查與 +2 制度內建） | [Gerrit](https://www.gerritcodereview.com/) | Apache-2.0 | 全流程（不用 GitHub 時） |

美國大公司內部那套多半不開源：Google 的 Critique／Tricorder、Meta 的 Phabricator 後繼與 RADAR、Uber 的 uReview 都是內部系統，公開的是論文與部落格。能拿到的開源對應：Gerrit（Google 血統）、Phorge（Phabricator 社群延續）、上表的 Danger／reviewdog／Semgrep／CodeQL／PR-Agent。本包的判級與交接契約可以直接落在 GitHub＋Danger＋reviewdog＋任一 AI reviewer 上，不需要換 review 系統。
