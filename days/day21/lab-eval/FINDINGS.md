# Day 21 Eval 發現（batch 20261003-044716，27 次，US$2.959）

正解與評分規則在跑之前固定（run-eval.py 的 EXPECTED）；契約用同一支 v2.0.2 gate.py，由外層執行。

## 結果
| 條件 | 語意（發送＋接收）| 誤判已送達 | 契約通過 | 平均回合 | 平均秒 | 平均 US$ |
|---|---|---|---|---|---|---|
| 不帶 Skill | 9/9 | 0/9 | 0/9 | 5.1 | 25.9 | 0.10 |
| v1（Day 17） | 9/9 | 0/9 | 0/9 | 7.0 | 27.7 | 0.11 |
| v2.0.2（Day 20） | 9/9 | 0/9 | 9/9 | 10.4 | 33.9 | 0.11 |

新案例 decoy-receipt（同訂單、不同通知 ID 的收據）三種條件 9/9 都判接收端 unknown。

## 讀法
1. **Skill 沒讓判斷變準**：不帶 Skill 一樣全對。這批案例對 Sonnet 5.5 太容易，不能用來證明 Skill 提升判斷。
2. **Skill v2 讓答案可被驗**：none／v1 的 evidence_refs 引用是對的（例如 `data/logs.jsonl:3 (notify_sent…)`），但為自由文字，gate 判 UNKNOWN_SOURCE_REF。v2 透過 collect.py 取得 `log:3` 這類機器可讀編號。
3. **不公平之處要講明**：契約格式由 v2 定義，none／v1 沒有工具產生 ref；「契約 0/9」量到的是「能不能交出可驗格式」，不是「判斷錯」。
4. **v1→v2 沒有退步**：三案例語意全對，回歸通過。
5. **成本**：v2 回合約兩倍、秒數多約 8 秒，費用持平。
6. complete 的 none／v1 另有 CONFIRMED_WITH_MISSING_SOURCE：接收端 confirmed 卻在 missing_sources 列了「Log server」等環境項，語意自相矛盾，只有程式抓得到。

## 限制
同一模型、同一台機器、每組 3 次；案例為教學資料。要證明 Skill 對判斷有用，需要更難、會讓不帶 Skill 失敗的案例。
