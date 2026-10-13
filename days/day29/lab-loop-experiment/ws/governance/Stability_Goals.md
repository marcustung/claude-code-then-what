# {{PRODUCT_NAME}} — 穩定性演化目標（Stability Evolution Goals）

> 狀態：第一版（v1）
> 定位：定義自演化的「安全邊界與健康指標」。《Evolution_Goals.md》管「往哪演化」，
> 本文件管「演化不能弄壞什麼」。每一輪演化落地前，必須通過六大 KPI 自我審查。
> **原則：不重造既有守門機制，而是把六大 KPI 對映到它們。**

---

## 1. 六大穩定性 KPI

每個 KPI 對映一組**可觀測訊號**與一種**自動提案機制**：訊號越過門檻時，
Agent 自動產生提案進 backlog（而非靜默忽略）。

| KPI | 可觀測訊號 | 提案範例 |
| :--- | :--- | :--- |
| **穩定性** | error 率/趨勢、task 失敗率、antipattern 復發率、規格 churn | 高復發 antipattern → 提案沉澱為硬規則 |
| **可管理性** | backlog 增長 vs 消化、未實作項堆積、模組邊界越界 | backlog 只增不減 → 提案排期或拆分 |
| **透明性** | 變更是否皆有紀錄（CHANGELOG/決策留痕）、audit 覆蓋率 | 有 diff 無紀錄 → 標違規並補登 |
| **可視化** | 狀態面新鮮度、有無彙整視圖、health-check | 缺彙整視圖 → 提案 health_report/dashboard |
| **安全性** | 過寬授權、缺冪等的資料變更、敏感欄位外洩、不可逆動作缺 gate | 過寬 scope → 提案收斂最小權限 |
| **生成真實性** | 未經佐證的輸出宣稱、文件宣稱與實體不符 | 宣稱與實體不符 → 提案校正 |

---

## 2. 對映到本系統（Concrete Mapping）

> 逐一把六大 KPI 對映到本系統的可量測點與**既有**守門機制。

### 2.1 穩定性 — {{STABILITY_SIGNALS_AND_GUARDS}}
### 2.2 可管理性 — {{MANAGEABILITY_SIGNALS_AND_GUARDS}}
### 2.3 透明性 — {{TRANSPARENCY_SIGNALS_AND_GUARDS}}
### 2.4 可視化 — {{OBSERVABILITY_SIGNALS_AND_GUARDS}}
### 2.5 安全性 — {{SECURITY_SIGNALS_AND_GUARDS}}
> 不可逆動作的硬邊界（鐵律）：{{IRREVERSIBLE_HARD_GATES，如：禁直接套 migration}}
### 2.6 生成真實性 — {{AUTHENTICITY_SIGNALS_AND_GUARDS}}

---

## 3. 健康門檻與觸發（Thresholds & Triggers）

| KPI | 黃線（提案） | 紅線（停止演化／升級人類） |
| :--- | :--- | :--- |
| 穩定性 | {{Y1}} | {{R1}} |
| 可管理性 | {{Y2}} | {{R2}} |
| 透明性 | {{Y3}} | {{R3}} |
| 可視化 | {{Y4}} | {{R4}} |
| 安全性 | {{Y5}} | {{R5}} |
| 生成真實性 | {{Y6}} | {{R6}} |

> **總則**：黃線 → Agent 自動產生提案進 backlog；紅線 → 停止自動落地、
> 報告顯著標記、整理提案升級人類。

---

## 4. AI 落地不可觸碰清單（迴路附錄）

> routine 落地時的硬邊界。提案觸碰任一項 → 自評風險 ≥ 8 並明確標註；
> 落地時觸碰到即中止回報。

1. {{UNTOUCHABLE_1，如：既有 API 回應格式}}
2. {{UNTOUCHABLE_2，如：DB schema／migration（需人工）}}
3. {{UNTOUCHABLE_3，如：domain 不變式與狀態機只能加強不能鬆動}}

## 5. 每輪落地自我審查清單（Gate）

- [ ] 六大 KPI 逐項通過（§1-3）
- [ ] 未觸碰 §4 清單；觸碰者已中止回報
- [ ] build／測試通過；新增測試對映提案 ID
- [ ] issue 檔拆解 checklist 如實勾選

## Day 29 實驗：不可觸碰清單（2026-10-04 定案，只由人修改）

- `acceptance/`（SPEC.md、run_acceptance.py）、`acceptance/LOCK.json` 鎖住的 70 個檔案
- `skill-lab/cases/`、`skill-lab/expected.json`、`skill-lab/eval.py`、`skill-lab/eval/gate/`
- `ops/data/`、`ops/scores/`（外層寫入）；出題程式、評分程式與事故答案已移出 repo，不得嘗試取得
- Gate 本身：不得提議拿掉人的核准；`approval-policy.json` 與本清單只由人修改
- AT-12 必須全程保持綠燈；告警不得靠關閉或放寬到永不觸發來降雜訊
- 產出只進 `ld/<id>` 分支，合併由人；第一期預算合計 ≤ US$50
- 不得自己執行 `skill-lab/eval.py`：Eval 會另外呼叫 18 次 claude、不受單輪上限管，由外層每天跑一次（`skill-lab/scores/`）
- 實驗 3 的考題、正解與評分程式已移出 repo（2026-10-05）；不得嘗試從 git 歷史（`git show`、`git log -p`）或磁碟其他位置取得 `skill-lab/cases`、`expected.json`、`ops-grader/`
