# Day 17｜操作附件：Log server 實跑與離線練習

[回正文](https://ithelp.ithome.com.tw/articles/10419500)

正文新增的 Log server 實跑使用本機 Docker，不含公司資料。先看[Log server 操作說明](lab-method-pack/log-server-lab/README.md)：啟動 Grafana、Loki 與 Alloy，產生新訂單 Log，再讓 Claude Code 載入 Skill、透過 MCP 查核三種情境。

修正後三案與 36 項檢查結果在 `lab-method-pack/log-server-lab/runs/live-20261001-02/verification-r2.json`；模型逐回合查詢在同目錄 `model/r2/`。失敗接入與修正前的紀錄也保留，見 [實驗對照](lab-method-pack/log-server-lab/RESULTS.md)。

以下保留不需要 Log server 的離線練習。collect.py 只整理本包格式，並非連接既有 Log 平台的必要元件。

## 離線先驗一件事：缺資料，不能被整理成零筆

這次選用的是 Day 16 補測裡「r2 配健康接收端」的紀錄，不是四次 503 的故障紀錄。它留下兩筆相關事件，以及一筆接收端實際收到通知的紀錄。

選成功案例有一個目的：如果把接收端紀錄拿掉，發送端仍會說成功。這時最容易把一邊的說法，誤當成兩邊已經對過。

測試資料分成兩份，原件保持不動：

| 測試輸入 | 腳本整理結果 |
|---|---|
| `complete`：Log 與接收端紀錄都有 | 兩笔相關事件、一筆接收端紀錄；兩個來源皆存在 |
| `missing-receipts`：只不提供接收端紀錄 | 仍有兩筆事件，接收端來源標成 `missing` |

第二組的接收端陣列也是空的，但旁邊明確記著來源缺失。**這和「確實取得一份紀錄，裡面沒有符合的資料」不是同一件事。** 只看陣列長度，兩者都會變成零。

整理器另外檢查了空集合、壞掉的 JSON 與不存在的訂單 ID，共七項本機檢查通過：完整資料能串起兩筆事件、對到一筆接收紀錄；缺件有標記且保留已有事件；空集合不當缺檔；格式錯誤獨立回報；其他訂單不混入。

這七項證明的是腳本如何整理資料，還不是 Claude 會不會照 Skill 判斷。

## 沒有連到 Log server，也能先用教學資料練習

方法包的[本機操作說明](lab-method-pack/README.md)附有兩組教學輸入。在 `examples/day17-method-pack/cases/complete` 開終端機，先執行：

```sh
python .claude/skills/trace-notification/scripts/collect.py .
```

它會在目前目錄產生 `evidence.json`。先看 `sources` 是否都有資料，再看 `events` 與 `receipts` 能不能對回原件。來源無效時會留下錯誤，不能把這份摘要當完整證據繼續使用。

接著在同一目錄開 Claude Code，用以下方式呼叫：

```text
/trace-notification
核對 task.json 指定的通知。請對照 evidence.json、原始紀錄、設計與程式，
分開列出已確認、仍未知，以及下一步需要取得什麼依據。
```

這是讀者可採用的操作方式，不是本篇已取得的模型執行結果。腳本由操作者或流程先執行；若模型只有讀取工具，就不能宣稱它自行跑了腳本。

驗證方法能否離開原對話，還要另開新 session，分別給完整資料與缺件資料，不附昨天的分析答案。我要核對的是：它是否真的載入方法、引用是否正確，以及缺接收端資料時，有沒有保留 `unknown`。

既有兩輪帶 Skill 與一輪不帶 Skill 的離線驗證已完成，保存於方法包根目錄的 runs/；三輪均保留缺件邊界。新增 Log server 驗證另存 log-server-lab/runs/，不覆蓋離線原件。兩者都沒有真人團隊採用或節省人工時間的證據。


## 版本界線

`cases/complete` 與 `cases/missing-receipts` 內的 SKILL.md 保留初版離線規則，供重現既有輸入；`package/` 的目前版則改成工具優先，整理器可選。七項檢查只對應 collect.py，不替任何一版 Skill 背書。模型驗證時須記錄選用哪一版，不能混算。
