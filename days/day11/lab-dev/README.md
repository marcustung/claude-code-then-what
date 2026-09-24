# 訂單取消：需求到交付的開發演練

這是 Day 9–16 重整後的新共同實跑。從固定 885e521 快照開始，接 Day9 範圍與 Day10 設計核對。不是早期 evidence/dev/day16 七步實驗，也不是正式系統或公司成效。

## 先看結果

| 工作 | 原件 | 已驗結果 |
|---|---|---|
| Claude 只改測試 | runs/tests | SC-03 FAIL，其餘六項 PASS |
| Claude 只改 Domain | runs/impl | 七項 PASS，diff 範圍符合 |
| API 邊界 | runs/integration-01 | 11項通過，含建置 |
| Day4 plugin 審查 | runs/plugin-review-01、02 | Skill 確實載入；兩次 OWNER_REQUIRED；誤報缺件更正，圖補上 |
| 本機 CI 入口 | runs/ci-local-01 | 分流自檢、Domain、整合成功 |
| 負向 CI | runs/ci-negative-01/fixture/runs/expected-red-02 | SC03失敗即停；首次搭建失敗另存不作證 |
| Package 啟動 | runs/package-smoke-01 | 十項通過，不含建置 |

## 不呼叫模型也能重跑

需要 Python 3、.NET 9 SDK。於本資料夾執行，各 run 使用新名稱：

```sh
dotnet run --project tests/DomainTests
python verify-integration.py reader-http-01
python ci.py reader-ci-01
dotnet publish src/Api/Api.csproj -c Release -o package-reader
python verify-integration.py reader-package-01 --artifact package-reader
```

驗證器只開本機 loopback 服務，停止本次啟動的程序。HTTP runner 使用暫時空閒 port，若被其他程序搶占會失敗，不把啟動失敗當成功。不要把這個未加正式認證的教學 API 對外暴露。

想回看先紅再綠：分別進 runs/tests/snapshot 與 runs/impl/snapshot，執行 `dotnet run --project tests/DomainTests`。前者預期退出1且SC03失敗，後者退出0；紅燈不是本範例壞掉。

## 想讓 Claude 再做一次

需已安裝並登入 Claude Code，這會消耗模型用量。

```sh
python prepare-rerun.py reader-01
cd reruns/reader-01
python run-development.py
```

不覆寫歷史，複製 baseline 建立新資料夾；保留模型 trace、diff、檔案快照、外層測試與來源雜湊。工具只准讀檔與修改，不提供 Bash；工具白名單不是檔案路徑防火牆，runner 另比對本次追蹤檔案的變動範圍。

## 規則與審查

CLAUDE.md 存規則及理由；plan.md 存本輪範圍。review-kit 為 Day4 原版0.1.0複本，Skill讀取證據在兩次trace。routing-policy.json 與 route-review.py 是另建的保守路徑政策，不是 skill 自動變成強制控制。

azure-pipelines.yml 是未遠端實跑的範本，labPath 須設為本包路徑。沒有配置遠端必要審查、合併或部署。

## 交付邊界

只本機、固定順序輸入、觀察窗口；不證明並行恰好一次、跨重啟持久性、真實金流、正式認證或其他人可部署。VERSION 沿原始快照保留，識別本次產物以 package-manifest 的hash為準，不假裝是原服務的新正式版本。

worklog.jsonl 依相同task_id記模型與runner時間；人工欄位null是未知，不是零，沒有省時結論。PR.md不是遠端PR或Owner批准。

## Day 11：有停止條件的提案／測試迴圈

```sh
python run-feedback-loop.py reader-loop-01 --max-rounds 3
python test-feedback-loop.py
```

第一條需登入 Claude Code 並消耗用量；第二條使用模擬模型回覆與真實 .NET 測試，不呼叫模型。新 run 名不能重複。

- 起點：`runs/tests/snapshot`（新測試、舊 Domain），固定測試應只在 SC-03 失敗。
- Claude 使用 Read/Grep/Glob，不提供寫入、shell 或 MCP 工具；回傳 status/reason/content JSON。外層只套用 Domain 檔，再跑 dotnet。
- 支援單一 JSON 程式區塊或純 JSON；格式錯誤即拒收。
- 情境失敗回送下一輪；三輪仍失敗回 ROUND_LIMIT；模型提出需要決策回 NEEDS_DECISION；編譯／環境／模型錯誤停止。CHECKS_PASSED 僅表示七個 Domain 情境通過。
- `feedback-loop-01` 保留格式拒收；`feedback-loop-02` 修正解析後重新呼叫，一輪通過。後者 `controller-tests.txt` 的四項通過是模擬回覆控制測試，非四次 Claude 實跑。
- 此 runner 用本機教學程式，不是 OS 沙箱；不要把不可信模型產出的程式直接放到有正式憑證的環境執行。未驗 API／通知／並行／人工接受。


## 後續日次

（各日的實驗會在該日發布當天補上。）
