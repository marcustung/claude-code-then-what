# plugin-lab：把 Day 3 的退件單做成 skill，考一次

2026-09-15。問題：把「第二位 Reviewer」的規則做成 Claude Code skill（`review-kit:review-pr`），跟不裝 skill 直接叫 Claude 審，差在哪？不是「有沒有載入」，是「有沒有比較一致、比較可查」。

## 材料

- `../plugin/review-kit/`：plugin（`plugin.json` v0.1.0）＋ skill `skills/review-pr/SKILL.md`。skill 四步：確定性閘門（diff 新增行含 Paid／Refund／authorized／`Cancelled =` 等就 OWNER_REQUIRED，模型不得降級）→ 五項交接契約逐項 filled／missing → 宣稱對證據（這一步就是 Day 4 歷史退件抽出來的 check-evidence 規則：每條宣稱要有來源，分清「沒查」與「查了不可用」，沒證據標 NEEDS_EVIDENCE）→ 八件深挖各答一句或寫 unknown。輸出固定 JSON。
- `fixtures/pr-A/`：Day 3 的訂單取消 PR，契約多欄空白、規則來源空白、作者自評 low。
- `fixtures/pr-B/`：同一份 diff，但 PR.md 與 ticket.md v2 附上 Owner 確認的 R-02／R-05／R-07，契約五項填滿。
- `check_card.py`：程式驗輸出，五條規則（R1 格式、R2 每則發現有來源、R3 無「看起來」類措辭、R4 diff 觸及閘門關鍵字則 verdict 必須 OWNER_REQUIRED、R5 契約五項齊）。
- `run-lab.ps1`：`claude -p`，sonnet、low effort、`--setting-sources ""`、只讀工具；S 條件加 `--plugin-dir` 與 Skill 工具。`extract_result.py` 從 trace 取結果與工具事件。

## 結果

| run | 裝 skill | Skill 工具有呼叫、有 Launching | verdict | 發現（block／ask／note） | 契約五項 | check_card | 回合／成本 |
|---|---|---|---|---|---|---|---|
| G0-A（無 skill，缺來源 PR） | 否 | — | OWNER_REQUIRED | 2／4／0 | 未檢查 | 通過（JSON 格式壞，程式修復後才能讀） | 5／$0.063 |
| S-A（skill，缺來源 PR） | 是 | 是 | OWNER_REQUIRED | 2／1／1 | 2 filled、3 missing | 通過 | 8／$0.133 |
| S-B（skill，有來源 PR） | 是 | 是 | OWNER_REQUIRED（閘門政策） | 0／2／2 | 5 filled | 通過 | 8／$0.069 |
| G0-B（無 skill，有來源 PR） | 否 | — | **NEEDS_EVIDENCE** | 0／1／1 | 未檢查 | **不通過：R4**（diff 觸及 Paid、`Cancelled =`，卻沒標 owner-required） | 5／$0.032 |

第一輪（`runs/round1/`）：pr-B 的 ticket.md 忘了改成 v2，PR.md 卻說 v2。**G0-B 抓到了**（3 個 block，含「ticket 未反映 v2」）；**S-B 沒抓到**（契約標 filled）。修 fixture 後重跑為上表第二輪。

## 讀法

- 不裝 skill，Claude 也會審，A 案也標了 OWNER_REQUIRED、也抓到假設沒人確認。**skill 不是讓它更會抓。**
- 差在一致：同一條政策（碰付款、狀態機就送 Owner），G0 在 A 案做到、B 案沒做到；skill 兩案都做到，因為那一步是寫死的第一步，check_card 又用同一條規則再驗一次。
- 差在可查：skill 的輸出每次同形（契約五項、閘門命中行號、八件事、Owner 問題、not_my_call），程式驗得過；G0-A 的 JSON 壞掉要修。
- skill 也會漏：第一輪 S-B 沒發現 ticket 版本不符，G0-B 反而抓到。載入不等於更準。
- 成本：skill 約 1.6–2 倍回合與費用。

## 不能說的

兩份 PR、六次 run、一個模型，不是正確率統計；沒有團隊使用、沒有減載證據；OWNER_REQUIRED 是閘門政策的結果，不是模型判斷力的證明。plugin 只以 `--plugin-dir` 載入本機原始碼，未走 marketplace 安裝（marketplace 安裝流程見 Codex 09-15 的 `writing/labs/2026-09-15-shared-review/`）。

## 重跑

```powershell
cd plugin-lab
.\run-lab.ps1            # 四個條件；或 .\run-lab.ps1 S-A G0-A
python extract_result.py
python check_card.py runs\S-A
```

## runs/demo-01（2026-09-17）

Day 5 讀者示範：pr-A、唯讀、無 plugin、`--output-format json`，5 回合、11,705 ms、$0.0474。見 `runs/demo-01/README.md`。


> 公開版：`runs/` 依天放在 `days/day04/lab-plugin/`（G0-B、S-A、S-B、round1、verify-20260918 的 V-G0-B／V-S-A）與 `days/day05/lab/`（G0-A、V-G0-A、demo-01）。`run-lab.ps1`／`run-verify.ps1` 重跑會在本目錄產生新的 `runs/`，不覆寫上述歷史 run。
