# {{PRODUCT_NAME}} — 進場守則

## 這個 repo 是什麼

{{PRODUCT_ONE_LINER}}

範圍：{{PRODUCT_SCOPE}}

## 進場必讀順序

任何 agent／協作者動工前，依序讀完：

1. `governance/SSOT.md` — 存在價值與邊界（單一事實來源）
2. `governance/Evolution_Goals.md` — 要往哪裡演化、KPI 與黃紅線
3. `governance/Stability_Goals.md` — 什麼絕對不能壞
4. `cs-loop/backlog/backlog.md` — 當前提案與裁決狀態
5. 最新一份 `cs-loop/health-reports/health-*.md` — 系統現況

## 鐵律（不可協商）

1. **main 上永不直改 app code。** 落地變更只能發生在 `land/<提案ID>` 分支，經 PR 進 main。
2. **絕不自動合併任何 PR。** 合併權在 {{OWNER_NAME}} 手上（Gate 2）。
3. **絕不修改 backlog「裁決」欄。** 核准權在 {{OWNER_NAME}} 手上（Gate 1）。routine 只能新增「待審」列。
4. 每日 routine 的產出（health report、backlog 新增待審列、CHANGELOG 回寫）**可以**直推 main——這些是治理文件，不是 app code。
5. 違反任何一條鐵律時，立即中止並回報，不要嘗試「補救」。

## 每日迴路

由 `.Codex/commands/cs-loop.md` 定義（八步：觀測 → 體檢 → 提案 → 自評 → 報告 → 落地 → 回寫 → 覆盤）。
排程 Trigger 每天觸發一次；人類透過 LoopDeck 裁決與合併。
框架級規則（分層模型、MVG、排程判準、生命週期）見框架憲法 FRAMEWORK.md（正本在 LoopDeck 工具 repo 的 templates/）。
