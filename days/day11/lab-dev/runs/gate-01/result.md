## 1. `ci.py` 每步失敗時如何讓流程停？退出碼怎麼傳？

`ci.py:7-10`：
```python
for name,cmd in [...]:
 p=subprocess.run(cmd,cwd=r,capture_output=True,text=True,...,timeout=180)
 (out/(name+'.txt')).write_text(p.stdout+p.stderr,...); steps.append({'step':name,'command':cmd,'exit':p.returncode})
 if p.returncode:break
```
- 每步用 `subprocess.run`（未加 `check=True`）取得 `p.returncode`，寫進該步的 `.txt` 和 `steps[]`。
- `ci.py:10` `if p.returncode:break` — 一旦某步非零就跳出迴圈，後面的步驟**不會被啟動**。
- `ci.py:11` `report['pass'] = len(steps)==3 and all(exit==0 ...)` — 只要迴圈提早中斷，`len(steps)<3`，`pass` 必為 `False`，不需要靠事後檢查退出碼。
- `ci.py:13` `raise SystemExit(0 if report['pass'] else 1)` — 這是傳回給呼叫端（`azure-pipelines.yml:14` 的 `python3 ci.py ...` script task）的最終退出碼。

**三步各自如何產生非零：**
- `route-review.py --selftest`：`assert` 失敗會丟 `AssertionError`，Python 對未捕捉例外預設以退出碼 1 結束（`route-review.py` 沒有 try/except 包裹 selftest 區塊）。
- `dotnet run --project tests/DomainTests`：`Program.cs:69` `return failures;` — **退出碼就是失敗的檢查數**，不是固定 0/1（`Program.cs:3` 註解也寫明「exit code = 失敗數」）。
- `verify-integration.py`：`main()` 最後 `return 0 if report['pass'] else 1`（第71行），再由 `if __name__=='__main__':raise SystemExit(main())` 傳出。

**可能被吞掉的地方：**
- `ci.py:8` 的 `subprocess.run(...,timeout=180)` **沒有**用 try/except 包住。若任一步逾時，會丟出 `subprocess.TimeoutExpired`，屬未捕捉例外 → 該步的 `.txt` 和 `report.json` **都不會寫出**（因為程式在寫檔前就已經中止）。這不是「吞掉」失敗訊號（退出碼仍非零），但會讓失敗證據不完整——沒有 `report.json`，只有一段 Python traceback。
- `verify-integration.py:61` `except Exception as e:check('runner',False,...)` 會把執行期例外轉成一筆失敗的 check，因此 `report['pass']` 仍會是 `False`——這不是吞掉，而是把例外「轉譯」成可讀的失敗記錄，是刻意設計。

## 2. 負向演練：換回舊版 Domain，預期在哪一步、哪一格失敗？

**這個演練在本專案裡已經真的做過一次**，證據在 `runs/ci-negative-01/`：
- `runs/ci-negative-01/fixture/diff.patch` 顯示把 `src/Domain/Cancellation.cs` 從 v2 邏輯（`refundRequested = order.Paid && !order.Cancelled`）換回 v1 邏輯（永遠 `RefundRequested: false`，對照 `baseline/src/Domain/Cancellation.cs`，`baseline/VERSION` = `1.2.0`）。
- 預期失敗位置：**`domain` 這一步、`SC-03`**（`tests/DomainTests/Program.cs:31-35` 「已付款取消要提出退款要求」），因為 v1 版本不會設 `RefundRequested=true`。
- 實測輸出（`runs/ci-negative-01/fixture/runs/expected-red-02/domain.txt`）：
  ```
  PASS SC-01 未出貨可取消，不要求退款
  PASS SC-02 已出貨不可取消，回傳原訂單
  FAIL SC-03 已付款取消要提出退款要求
  PASS SC-04 未付款取消不要求退款
  PASS SC-05 已出貨已付款不可取消，不要求退款
  PASS SC-06 已取消再次取消維持原狀（未付款）
  PASS SC-07 已取消再次取消不重複退款（已付款）
  FAIL: 1 項條件未通過
  ```
- 對應 `report.json`（同目錄）：`routing-selftest` exit 0，`domain` exit 1，**`integration` 完全沒被啟動**（`steps` 只有 2 筆）——與 `ci.py:10` 的 `break` 邏輯一致。`rerun-report.json` 的摘要也寫著：`"checks": "routing succeeded; domain failed SC-03; no integration launched"`。

所以你要做同樣的演練，可以直接參考這份既有紀錄——不必猜，是已發生過的觀察。

## 3. 有沒有「也回非零、但根本沒跑到測試」的失敗？怎麼分辨？

有，而且這個資料夾裡就有一個真實案例，不是假設：

`runs/ci-negative-01/output.txt` 記錄了一次 `ci.py` 執行，內容是 Python traceback：
```
FileNotFoundError: [WinError 3] ...找不到指定的路徑: '...\runs\ci-negative-01\fixture\runs\expected-red'
```
發生在 `ci.py:6` 的 `out.mkdir(parents=True,exist_ok=False)`（此處是巢狀呼叫 `fixture/ci.py`，其父目錄不存在）。這發生在**進入三步迴圈之前**，所以：
- 沒有任何 `.txt` 或 `report.json` 被寫出（`runs/ci-negative-01/report.json` 是後來**手動**補寫的摘要，schema 是 `{"exit":1,"pass":false,"reason":"fixture runs parent missing; did not execute gate. Retained as harness setup failure."}`，跟 `ci.py` 自己產生的 report schema（`steps/pass/elapsed_seconds/human_minutes/remote_ci/business_accepted`）明顯不同）。
- 退出碼仍是非零（Python 對未捕捉例外預設回傳 1），但意義是「腳本本身壞了」，不是「測試沒過」。

**分辨方法**：看輸出證據裡有沒有 `report.json` 且其中的 `steps` 陣列是否存在、每步是否有對應的 `.txt`：
- 真正跑到測試並失敗：有 `report.json`，`steps` 裡列出已執行步驟與各自 `exit`，且對應步驟有 `.txt` 內容（如 SC-01~07 的 PASS/FAIL 列表）。
- 根本沒跑到：stdout/stderr 是一段 Python traceback（`Traceback (most recent call last):` 開頭），沒有 `report.json`，或 `steps` 陣列是空的/缺某幾步的 `.txt`。

另外提醒：`subprocess.run(...,timeout=180)` 若逾時，性質相同——也是「非零但沒跑完」，特徵同樣是缺 `report.json`。

## 4. `azure-pipelines.yml` 跟本機 `ci.py` 之間，本機有、遠端不一定有的東西

逐項列出（依 `azure-pipelines.yml` 內容）：

1. **`trigger: none`（第2行）**：這條 pipeline 不會因 push/PR 自動觸發，且檔案開頭註解明寫「範本，未在遠端執行」（第1行）。也就是說目前這份檔案**從未在 Azure DevOps 上真正跑過**——本機三步全綠不能推論「遠端也會綠」，因為遠端根本沒被驗證過。
2. **`pool: vmImage ubuntu-latest`（第7-8行）** vs 本機是 Windows（環境資訊：`Platform: win32`，且 `runs/ci-negative-01` 的 traceback 路徑也證實是 Windows 執行）。作業系統不同，若 Domain/API 程式碼中有任何依賴平台行為（例如路徑分隔符、檔案編碼、換行符），本機綠不代表遠端會綠。目前讀到的程式碼是用 `pathlib`／標準函式庫，看起來是跨平台寫法，但**我沒有逐行審過 `src/Api`、`src/Domain` 全部程式碼去排除平台差異**，這部分是推論而非窮舉驗證。
3. **`UseDotNet@2 version: '9.x'`（第10-13行）**：遠端明確釘住 .NET 9.x SDK；本機沒有找到 `global.json` 來釘版本，代表本機用的是「當前安裝的 dotnet」。若本機 dotnet 版本跟遠端 9.x 有落差（例如本機是 9.0.10x 但遠端裝到 9.0.10y 有行為差異），本機綠不保證遠端綠。這點是推論，因為我沒有實際比對兩邊 SDK 版號（本機沒跑指令查詢）。
4. **`python3 ci.py ...`（第14行）**：遠端用 `python3`；本機（依 `output.txt` 的 traceback）用的是 `<HOME>\...\python.exe`（Python 3.14）。若遠端 ubuntu-latest 內建的 python3 版本較舊，且程式碼用到本機版本特有語法，可能出現本機過但遠端解析失敗的落差——這也是推論，`ci.py` 本身語法很基礎，實際風險應該低，但沒有在遠端驗證過。
5. **`labPath` 參數（第3-6行，預設 `.`）**：遠端執行依賴呼叫端正確帶入這份教學包所在的相對路徑；本機執行 `ci.py` 時工作目錄就是專案根目錄，不存在這個參數解析的風險。若遠端呼叫方設錯 `labPath`，會在完全不同的錯誤點失敗（找不到 `ci.py` 或找不到 `route-review.py`），這種失敗甚至不會產生任何 `runs/*/report.json`（同第3點的「沒跑到測試」情境）。
6. **NuGet 還原（restore）**：本機的 `src/Domain/obj`、`tests/DomainTests/obj` 已經有本機還原快取（我在 Glob 結果裡看到 `project.assets.json`、`project.nuget.cache` 等檔案），代表本機執行 `dotnet run` 時很可能是用既有快取、速度快。遠端 ubuntu-latest 每次是全新 VM，第一次一定要連網路做完整 restore，時間會比本機長很多，`ci.py:8` 的 `timeout=180` 秒對本機夠用，但**遠端是否夠用、遠端 NuGet 來源是否可連通，我沒有證據可以確認**——這是明確的推論缺口。
7. **`condition: always()` 發佈 artifact（第18行）**：這點遠端有、本機沒有對應機制——本機執行完只是留在本地 `runs/` 資料夾；遠端會把 `runs/` 整包發佈成 `verification-evidence` artifact，即使流程失敗也會發佈。這是遠端「多出來」而非「本機有遠端沒有」的東西，但值得注意：它讓遠端失敗時的證據保存比本機更制度化。
8. **檔尾註解（第22行）**：「這是驗證流水線，不含部署。Owner 必要審查須另在 repo 政策設定。」——這代表就算這條 pipeline 全綠（假設哪天真的跑起來），也**不等於**有任何機制真的擋下未經 Owner 審核的 `OWNER_REQUIRED` 路徑變更。`route-review.py --selftest`（`route-review.py:9-13`）只驗證路由判斷邏輯本身對不對，它不是分支保護規則，沒有接到任何實際擋 PR 的機制。這件事本身是從檔案讀到的（註解直接寫明），但「因此遠端全綠不等於已有人審過核心路徑變更」是我根據這行註解做的推論。

---

### 來源 vs 推論

**直接讀到、有檔案依據：**
- 第1題全部退出碼傳遞邏輯（`ci.py:6-13`、`route-review.py:9-13`、`verify-integration.py:61,69,71-72`、`tests/DomainTests/Program.cs:3,68-69`）。
- 第2題的期望失敗訊息與斷點位置——**不是我推測的，是 `runs/ci-negative-01/` 資料夾裡既有的實測紀錄**（`diff.patch`、`domain.txt`、`report.json`、`rerun-report.json`）。
- 第3題的「沒跑到測試也非零」案例——同樣是既有的真實紀錄（`runs/ci-negative-01/output.txt` 的 traceback + 手動補寫的 `report.json`），不是假設情境。
- 第4題第1、2、3、5、7、8點直接讀自 `azure-pipelines.yml` 逐行內容。

**推論、且依據不足之處：**
- 第4題第2點「程式碼跨平台安全」：只掃過本次讀到的檔案，沒有逐行審查 `src/Api`、`src/Domain` 全部原始碼，不能排除平台相關的隱藏差異。
- 第4題第3點「dotnet 版本落差風險」：本機沒有 `global.json`，也沒有實際執行指令比對本機與遠端 SDK 版號，純屬合理推測。
- 第4題第6點「遠端 restore 逾時風險」：沒有任何遠端執行紀錄可查，純粹根據「本機已有快取、遠端是全新 VM」這個結構性差異推論，不能證明一定會逾時或成功。
- 未讀到 CI 在遠端實際跑過的紀錄（`trigger: none` 且註解明講「未在遠端執行」），所以本題所有「遠端會怎樣」的推論都只能到「結構上可能造成落差」，不能宣稱遠端一定會壞或一定會過。