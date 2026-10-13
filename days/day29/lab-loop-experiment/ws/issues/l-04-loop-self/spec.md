# l-04-loop-self|實驗4 優化平台自己：依迴圈紀錄調整做事方式

【目標】
週期性依框架觀測 SSOT，比對「演化目標 vs 現況」的差距，每輪產出 1~N 張提案議題（state=review）進看板，由人逐案裁決後才執行。

【約束】
- 不得提議拿掉人的核准（Gate 本身）（Stability_Goals 煞車）
- 不得碰硬邊界與不可觸碰清單、驗收測試、Eval 案例、指標定義（tools/loop-metrics.js）（Stability_Goals 煞車）
- approval-policy.json 只能提議，由人修改（Stability_Goals 煞車）
- 每輪預算 ≤ US$1（Stability_Goals 煞車）
- 觀測與回寫的錨點只有 SSOT：`ws/metrics/loop-metrics-*.json（node tools/loop-metrics.js --since 2026-10-07 產出）`（repo-native（git 可讀））
- 每輪只產提案（state=review），不產 code diff、不開分支；落地一律走人類裁決後的派工

【驗收】
1. 每輪產出的提案議題都附【證據】段（引用 SSOT 出處），可被逐案裁決
2. 本輪執行在該 routine 的 runs/ 留痕完整（成敗、產出、成本）

<!-- loopdeck:framework -->
## 迴路框架（三柱，由 LoopDeck 維護）

- **flavor**：loop engineer
- **執行時間（cron）**：`30 1 */3 * *`
- **SSOT（地基）**：`ws/metrics/loop-metrics-*.json（node tools/loop-metrics.js --since 2026-10-07 產出）`（repo-native（git 可讀））

**Evolution_Goals（油門）**——這迴路要持續把 SSOT 推向的方向

- 降低每日裁決分鐘數與退回率
- 提高自評風險與裁決的一致性
- 可提議：提案範本、切分大小、自評標準、某類提案的核准等級、節流門檻、覆盤頻率

**Stability_Goals（煞車）**——演化過程不得破壞的護欄

- 不得提議拿掉人的核准（Gate 本身）
- 不得碰硬邊界與不可觸碰清單、驗收測試、Eval 案例、指標定義（tools/loop-metrics.js）
- approval-policy.json 只能提議，由人修改
- 每輪預算 ≤ US$1

<!-- /loopdeck:framework -->
