I have enough now to give a well-sourced answer. Compiling the report.

## 回報：五題 + 交接缺口

**方法**：只讀了這個資料夾裡的檔案（CLAUDE.md、plan.md、specs/、design-input/、src/、tests/、runs/*/result.md 與其 report.json/txt、review-kit skill）。沒有執行任何指令、沒有修改任何檔案。

---

### 1. 這次改了哪一條業務規則？依據？舊/新行為？

**規則**：BR-03（改）——已付款、尚未出貨的訂單取消時，**要**提出退款要求。
- 來源：`specs/rules-v2.md:11`（表格 BR-03 列），註明「Owner 推翻 v1 決定第 3 列」。
- 舊行為（v1，`specs/decisions-v1.md:7`）：已付款、未出貨取消 → `RefundRequested=false`。
- 新行為（v2）：同條件 → `RefundRequested=true`（`specs/rules-v2.md:21` SC-03）。
- 另新增 BR-04（`specs/rules-v2.md:12`）：已取消訂單再次取消 → 維持原狀、`RefundRequested=false`、不丟例外，這是「補 v1 待確認項」（v1 對此標「待確認」，見 `specs/decisions-v1.md:9`）。

程式現況：`src/Domain/Cancellation.cs:19` 目前是 `refundRequested = order.Paid && !order.Cancelled`，即 v2 邏輯。但要指出一個矛盾：`runs/tests/snapshot/src/Domain/Cancellation.cs`（2026-09-21 執行時的快照）顯示的是**舊 v1 邏輯**（固定回傳 `false`），而 `runs/impl/result.md:14` 記錄了把它改成 v2 邏輯的動作。也就是說，資料夾裡現在的 `src/Domain/Cancellation.cs` 是「改完之後」的版本；`source-manifest.json:4` 的 sha256（`858cb0e0...`）跟 `runs/package-smoke-01/report.json:186` 記到的 sha256（`46de39fe...`）不一致，代表 `source-manifest.json` 記的仍是**改動前**的雜湊，尚未更新。

### 2. 哪些已經被實際執行驗證過？哪些只在文件上？

**已有執行紀錄（有 exit code / stdout 檔案佐證）：**
- 紅燈：`runs/tests/tests.txt:1-8` —— 對舊 Domain 跑 SC-01~07，SC-03 FAIL，其餘 PASS。
- 綠燈：`runs/impl/tests.txt` —— 改完 Domain 後跑，7 項全 PASS。
- 負向演練：`runs/ci-negative-01/fixture/runs/expected-red-02/domain.txt` —— 把 Domain 換回 v1 邏輯重跑，確認 SC-03 會 FAIL、`report.json` 顯示 integration 步驟因此沒被啟動。
- 整合/HTTP 層：`runs/integration-01/report.json`、`runs/package-smoke-01/report.json` —— 對跑起來的 API 打 `/orders/{id}/cancel` 等，各情境（已付款、未付款、已出貨、重複取消、401、通知 payload、log）皆 `pass: true`。`package-smoke-01` 是對**打包後**的 artifact 跑，`source_sha256`/`artifact_sha256` 有記錄。

**只在文件上、未見執行證據：**
- `CLAUDE.md:9` 明講「本次由外層 runner 執行測試」——本 agent（我或前幾輪 result.md 的作者）本身**沒有執行過**任何指令，僅依 spec 推演或讀既有 runner 產出的檔案。
- 並行取消安全、重啟後佇列持久性：`design-input/design-review.md:4-5` 只是文字結論（「read/decide/write 非整體原子」「檔案日誌不等於記憶體佇列」），`runs/package-smoke-01/report.json:189` 的 `limits` 欄也明講「no ... concurrent exactly-once or restart recovery」——**沒有任何一次執行測過**這兩項。
- Azure Pipelines 遠端 CI：`runs/gate-01/result.md:66` 指出 `azure-pipelines.yml` 是 `trigger: none` 的範本，「從未在 Azure DevOps 上真正跑過」——本機綠不代表遠端會綠，這只是推論。
- 完整 repo 呼叫端/依賴影響範圍：`design-input/scope-handoff.md:24`「本包沒有 caller；完整 repo 影響範圍仍需補查，不得宣稱不存在依賴」——沒查過，不是「查過確認沒有」。

### 3. 使用者按下取消之後，通知保不保證送到？

**資料夾裡找不到「保證送到」的依據；現有機制是 at-least-once 重試 + 失敗即死信，不是保證送達。**

依據 `src/Api/Program.cs`：
- 正常路徑通知先入列（`channel.Writer.WriteAsync`，第84行）再回應（第89行），HTTP 200 不代表通知已送達，只代表已入列（`design-input/design-review.md:1`：「Worker 的送達與 HTTP 回應沒有固定先後」）。
- `NotificationWorker.ExecuteAsync`（第210-253行）對送達失敗會重試 3 次（200/400/800ms backoff，第188行），超過上限進 `notify_dead_letter`（第249-250行）——即**送不到就進死信、不再保證送達**，只留一筆 ERROR log。
- 有故障注入路徑 `notify_drop_over_queue`（第215-225行）會把通知延後重排，最多 `MaxDeferrals=5` 次，超過後才走一般重試——這是演練用（第181行註解：「演練用注入，不是自然事故」），不是正式保證機制。
- `design-input/design-review.md:6`：「notification 決策表並非全部 proposed；有沿用項」——代表通知相關的正式決策表本身狀態不明確，資料夾裡沒有一份「通知契約」文件確認保證語意。

結論：**現有程式是盡力送達＋失敗即死信，沒有「保證送達」的實作或文件承諾**。

### 4. 現在可以部署到正式環境嗎？

**不行。** 依據：
- `runs/plugin-review-02/result.md:6,48` review-kit 兩輪審查結論都是 `"verdict": "OWNER_REQUIRED"`，且明講政策性 gate（`Paid` 關鍵字命中）「無法被本次審查解除」（`review-kit/skills/review-pr/SKILL.md:8`：第二審查者「不能解除任何 owner-required 要求」）。
- 未解決的 block/ask 項（`runs/plugin-review-02/result.md:43-73`）：
  - BR-03 反轉是否已有「正式合併」層級的 Owner 核准，還是只到教學示範層級（`specs/rules-v2.md:3` vs `design-input/scope-handoff.md:3` 明講「不是作者業務核准」）——severity: **block**。
  - `design-input/scope-handoff.md:23` NC-02 與 decisions-v2.1 矛盾未決。
  - 完整 repo 呼叫端影響範圍未查（`scope-handoff.md:24`）。
  - 並行取消/重啟持久性未驗證（`design-review.md:4-5`）。
- `azure-pipelines.yml` 從未在遠端真正跑過（`runs/gate-01/result.md:66`），本機綠燈不能推論遠端綠燈。
- `plan.md:8` 本身就寫明「本機封裝與啟動，不冒充遠端CI或正式部署」——這條規則本身就排除了把目前產物當成部署證據。

### 5. 哪些事我不能自己決定、必須找人？找誰、決定什麼？

依 `runs/plugin-review-02/result.md:85-92`（owner_questions / not_my_call）與相關文件：

| 事項 | 找誰 | 決定什麼 |
|---|---|---|
| BR-03 反轉是否已滿足「正式合併」的業務核准，還是僅教學示範層級確認 | 訂單 Owner | `specs/rules-v2.md:3` 的確認範圍是否涵蓋這次要合併的 PR |
| `Paid` 關鍵字觸發的政策性 OWNER_REQUIRED gate | Owner（政策程式擁有者） | 是否豁免此次 diff；`plan.md:7`「政策程式另查，模型不能解除」 |
| NC-02 與 decisions-v2.1 的回應矛盾 | Owner | 通知回應行為該以哪份為準 |
| 完整 repo 呼叫端/依賴影響範圍尚未查 | Owner／原服務維護者 | 是否需要先做全 repo 影響分析才能視為範圍已確認 |
| 並行取消與重啟後佇列持久性未驗證 | Owner／工程 | 這個已知風險是否可接受、還是要擋在合併前 |
| 通知保證語意（送達保證、死信後續處理） | Owner | 目前 at-least-once＋死信是否符合業務期待，若不夠要不要立案 |
| 是否/何時真的部署到正式環境、走遠端 CI | Owner／SRE | `azure-pipelines.yml` 從未執行過，誰來啟用、誰審核 |

---

### 接手這個服務之前，我還需要什麼這裡沒有的東西

- 一份「通知契約」正式文件（誰承諾送達語意、死信後的人工/自動處理流程）——目前只有程式行為，沒有契約文件。
- 完整 repo（不只這個教學包）的原始碼與依賴圖，確認這個 Domain 有沒有其他呼叫端。
- Owner 對「教學示範確認」與「正式合併核准」是否等同的明確書面回覆。
- 實際跑過一次的遠端 CI（Azure Pipelines）紀錄，而不是 `trigger: none` 的範本。
- 並行取消、服務重啟後佇列/通知持久性的專門測試與結果。
- `source-manifest.json` 需要重新產生（目前記的 Cancellation.cs 雜湊是改動前版本，與 package-smoke 實際使用的雜湊對不上）。
- NC-02 與 decisions-v2.1 矛盾的正式裁決紀錄。
- 值班/on-call 聯絡方式與正式的事故處理手冊（本資料夾未提供，我完全找不到）。