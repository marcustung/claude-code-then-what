# cs-loop 治理骨架模板

這個目錄是「cs-loop 人在環治理慣例」的泛用骨架。要在新專案套用同一套機制，
把這裡的檔案複製到目標 repo，把 `{{PLACEHOLDER}}` 換成產品相關內容即可——
鐵律、八步迴路（含覆盤）、雙 Gate、去重/節流機制都已內建，不用重新設計。

> **框架憲法**：分層模型、排程判準、資產三問、迴路生命週期、框架修訂規則
> 見本目錄的 [`FRAMEWORK.md`](FRAMEWORK.md)——它是框架自身的單一事實來源，
> **不隨骨架複製到各 repo**（避免框架版本漂移），各 repo 以引用方式遵循。

## 新迴路啟動檢查清單（MVG，Minimum Viable Governance）

> **排程（心跳）只是迴路的觸發器；迴路的核心是三件套。** 下列四項硬前置
> 缺一就不該讓排程開始每天 run——缺了會造成方向錯誤或安全風險：

- [ ] **北極星一句話**（SSOT §1.1）——沒有它，agent 每天提案是亂槍打鳥
- [ ] **3-5 個 outcome 型輸入指標＋黃紅線**（Evolution §1.1）——每日體檢量什麼的定義；
      不可用活動量（commit 數、卡片數）冒充；尚不可量測就誠實標註
- [ ] **不可觸碰清單**（Stability §4）——沒有它，agent 會碰禁區
- [ ] **雙 Gate 權限宣告**（SSOT 附錄）——誰核准、誰合併

可以邊跑邊長的（不擋啟動）：價值鏈完整拆解、指標補齊、六大穩定性 KPI 完整對映、
回寫規則細化——這些本身就在迴路的回寫治理範圍內。

啟動後：到 LoopDeck 的 `loops.json` 註冊迴路 → 建排程（本機工作排程器
或雲端 routine）→ 每天在 Console 裁決與審核。

## 套用步驟

1. 把整個目錄結構複製進目標 repo 根目錄：

   ```
   CLAUDE.md
   CHANGELOG.md
   .claude/commands/cs-loop.md
   governance/SSOT.md
   governance/Evolution_Goals.md
   governance/Stability_Goals.md
   cs-loop/backlog/backlog.md       （狀態索引：四區表格＋裁決欄）
   cs-loop/issues/                  （一案一檔：背景全文＋拆解 checklist＋裁決/落地記錄；
                                     issue-template.md 是格式範本，不用改名）
   cs-loop/health-reports/          （放每日報告；health-template.md 是格式範本，不用改名）
   ```

2. 全域搜尋 `{{`，把所有佔位符換掉：

   | 佔位符 | 意義 |
   | --- | --- |
   | `{{PRODUCT_NAME}}` | 產品／系統名稱 |
   | `{{PRODUCT_ONE_LINER}}` | 一句話說明這個 repo 是什麼 |
   | `{{PRODUCT_SCOPE}}` | 系統邊界：管什麼、不管什麼 |
   | `{{OWNER_NAME}}` | 治理負責人（握雙 Gate 的人） |
   | `{{KPI_1}}`…`{{KPI_6}}` | 六大 KPI 名稱 |
   | `{{KPI_n_YELLOW}}` / `{{KPI_n_RED}}` | 各 KPI 的黃線／紅線門檻 |
   | `{{KPI_DATA_SOURCES}}` | routine 觀測步驟要去哪裡撈 KPI 原始數據 |
   | `{{EVOLUTION_GOAL_*}}` | 中長期演化目標 |
   | `{{STABILITY_BOUNDARY_*}}` | 不可破壞的穩定性邊界 |

3. commit 進 main，然後：
   - 在 Claude Code 建立每日排程 Trigger（LoopDeck 的「排程設定」分頁有教學與可複製的 prompt）。
   - 在 LoopDeck 的 Settings 指到這個 repo，即可用網頁介面裁決與合併。

## 不要改的東西

- CLAUDE.md 的「鐵律」段落與 cs-loop.md 的七步結構——這是機制本體。
- backlog.md 的四區結構與「裁決」欄——Console 與 routine 都依賴這個格式。
- 表格內若要寫字面 `|`（例如 grep pattern），必須跳脫成 `\|`。
