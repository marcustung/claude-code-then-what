# r-01-acceptance-report|實驗1 對照組：驗收測試日報

【目標】
週期性觀測 SSOT，產出一份唯讀報告落 reports/——不開任務、不需逐次裁決、不落地任何 code（platform-spec §2.1 的退化型）。

【約束】
- （唯讀觀測，不寫回 SSOT）（Stability_Goals 煞車）
- 觀測與回寫的錨點只有 SSOT：`order-service/acceptance`（repo-native（git 可讀））
- 只產報告，不開任務、不落地任何 code

【驗收】
1. 每輪在 reports/ 產出一份可讀報告，內容可回溯到 SSOT
2. 本輪執行在該 routine 的 runs/ 留痕完整（成敗、產出、成本）

<!-- loopdeck:framework -->
## 迴路框架（三柱，由 LoopDeck 維護）

- **flavor**：report
- **執行時間（cron）**：`0 3 * * *`
- **SSOT（地基）**：`order-service/acceptance`（repo-native（git 可讀））

**Evolution_Goals（油門）**——這迴路要持續把 SSOT 推向的方向

- （report routine 的退化型：只觀測、不驅動，無油門）

**Stability_Goals（煞車）**——演化過程不得破壞的護欄

- （report routine 的退化型：唯讀產報告，無煞車）

<!-- /loopdeck:framework -->
