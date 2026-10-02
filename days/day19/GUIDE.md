# Day19 操作附件：查核結果的固定檢查

教學包：`examples/day19-result-gate/`。使用 Python 3 標準函式庫，固定檢查不需安裝套件、Docker 或呼叫模型；`run-model.py`、`model-check.py` 才會呼叫 Claude Code。

## 檔案與信任邊界

| 檔案 | 用途 |
|---|---|
| result-contract.md | 新增的結果格式與可補進既有 Skill 的輸出要求 |
| task.json | 教學任務的預期ID與版本 |
| evidence.json | SYNTHETIC 來源清單，由本次作者固定建立，不是新抓到的Log |
| fixtures/ | 十二份預先定義的結果，包含錯誤與語意反例 |
| cases.json | 每份案例預期退出碼、狀態與錯誤碼 |
| check_result.py | 固定條件檢查，不呼叫模型與網路 |
| run_gate.py | 執行檢查、保存雜湊、標記去向；沒有外部派送 |
| run_cases.py | 逐案呼叫真正CLI，比對預期與實際 |
| run-model.py | 讓 Claude 唯讀讀取任務與來源清單，產出結果 JSON 再送進入口（需 Claude Code CLI） |
| model-check.py | 13 案各 3 次，讓模型當檢查器，結果寫入 runs/model-checker/（需 Claude Code CLI） |
| original/ | Day17完整回答副本、抽出的原JSON、用新契約檢查的結果 |
| runs/ | 每次另建時間目錄，不覆蓋前次結果 |

Day17的接收端來源在文字裡；original/evidence-empty.json只是表示沒有建立機器可讀對照，不表示歷史查詢沒有取得Log。舊JSON缺四項新欄位，是契約版本差異，不能判成Day17模型出錯。

## 在本機執行

先切換到教學包目錄。

```text
python run_cases.py
```

本次輸出 cases=12、matched=12。詳細表在 `runs/20261002-013027-964123/report.json`。八個案例退回，三個 READY_FOR_REVIEW、一個 NEEDS_FOLLOWUP。matched 是符合預設結果，不是模型正確率。

逐步演練退回與補齊：

```text
python run_gate.py fixtures/02-missing-receiver.json task.json evidence.json
python run_gate.py fixtures/12-repaired.json task.json evidence.json
python run_gate.py fixtures/05-unknown.json task.json evidence.json
```

依序退出碼為 1、0、0。每次 result.json 保存 `check`、`checker_exit`、`next_queue`。第一份 next_queue=null；第二份 human-review；第三份 needs-followup。這些只是本機標記，external_dispatch=false，並未真的建立待辦。

若使用PowerShell自動串接其他命令，必須先判斷 `$LASTEXITCODE`；不能忽略1而照樣執行下一步。正式工作系統也須強制使用入口，單獨存在一支腳本不防止繞過。

## 重要的語意反例

```text
python run_gate.py fixtures/11-bad-advice.json task.json evidence.json
```

它會通過格式與證據欄位檢查，因為next_action只有非空驗證，不能理解「立即補送並結案」是否有權執行。approved始終false，不提供任何副作用工具。因此結果需由指定人核對，不能把下一步文字當命令。

## 未完成的整合

固定檢查之外，已另有兩次直接提示模型產生新契約輸出及 39 次模型當檢查器的紀錄；這些不是載入 Skill 的完整 Eval，也沒有讀取即時 Log。若接入Day17流程，須新增工具結果到來源清單的adapter，保存查詢範圍、時間窗、版本及原始回傳，再由Claude引用其編號；模型不可覆寫來源。接著才驗證實際載入、新格式輸出與自動觸發檢查。不能把本機固定案例改寫成已完成端到端。

此檢查器限定本包資料結構，不驗完整schema、時間窗、部署身分、來源真偽與語意正確性。人工工時與token效益未量測。固定腳本不呼叫模型，不代表整條流程沒有模型用量。


## 模型試跑與正文的關係

主線是 Claude、程式與人的分工，Eval 作為取捨的證據。既有兩次生成與39次判定不冒充 Skill 的改版回歸。

- 生成紀錄：runs/model-complete/ 與 runs/model-decoy/；前者4回合、5.4秒、約US$0.019，後者4回合、7.4秒、約US$0.016（沿用既有紀錄，不是本輪重跑）。
- 判定實驗：runs/model-checker/summary.json，13案、每案3次，39次符合預期；平均模型費用US$0.0126。
- 輸出JSON、完整條件與語意反例保留在 result-contract.md、fixtures/、cases.json。
- 程式不呼叫模型，不代表開發、運算、維護總成本為零。未量測端到端節省。

## 接回 Skill 的輸出要求（待整合）

```text
回傳 result-contract.md 規定的 JSON。
通知 ID 與版本取自任務；evidence_refs 只引用工具留下的來源編號。
接收端無依據時保留 unknown，列出缺件與下一步。
檢查失敗只能補查或修正結論，不得修改 task、來源紀錄或檢查器來通過。
```

提示不能替代權限。工作流程須在收到結果後固定執行 run_gate.py，再處理退件或待查。若使用 Hooks，須另核對事件輸入與停止語義，這裡沒有安裝可直接使用的 Hook：[官方 Hooks 指引](https://code.claude.com/docs/en/hooks-guide)。

Skill 可留查法與腳本入口；Harness 負責何時執行、使用什麼權限、結果保存與失敗去向。本包只完成其中本機核對與分流的一段。
