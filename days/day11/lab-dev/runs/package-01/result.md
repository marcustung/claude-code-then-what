## 1. 從發布產物啟動 vs. 從原始碼啟動，執行時可能不一樣的地方

先澄清一個關鍵事實：`verify-integration.py` **本身從未使用 `dotnet run`**。不論有沒有 `--artifact`，它一律用 `dotnet <路徑>/Api.dll` 啟動進程（`verify-integration.py:36`）；差別只在於：
- 沒給 `--artifact` 時，先跑 `dotnet build src/Api/Api.csproj`（`verify-integration.py:33`），執行檔取自 `src/Api/bin/Debug/net9.0/Api.dll`（`verify-integration.py:20`）。
- 給了 `--artifact` 時，跳過 build，直接用 `<artifact>/Api.dll`（`verify-integration.py:20,32`）。

逐項可能的差異：

- **Debug vs Release**：`dotnet build` 預設 Debug、`dotnet publish` 預設 Release，`Api.csproj` 沒有覆寫 `Configuration`（`src/Api/Api.csproj:2`）。這會影響最佳化與 tiered JIT，`Program.cs` 沒有任何 `#if DEBUG` 分支，功能邏輯理論上一致，但這點沒有源碼證據能保證兩者輸出位元組完全一致。
- **cwd 相同、但 BaseDirectory 不同**：`Program.cs:12` 讀 VERSION 檔是用 `AppContext.BaseDirectory`（即可執行檔所在目錄），不是 `cwd`。`verify-integration.py:36` 兩種模式都把 `cwd` 設成 `ROOT`，但 `AppContext.BaseDirectory` 會分別指向 `bin/Debug/net9.0/` 或 `--artifact` 指定的發布目錄。只要兩邊都有 VERSION 檔（`Api.csproj:4` 的 `CopyToOutputDirectory` 對 build 和 publish 都適用），這點理論上不會造成差異，但沒有驗證。
- **web.config 只在 publish 產物出現**：manifest 列出 `web.config`（`package-manifest.json:11`），這是 `Microsoft.NET.Sdk.Web`（`src/Api/Api.csproj:1`）在 publish 時自動產生、給 IIS/ANCM 用的檔案。但 `verify-integration.py` 兩種模式都是直接用 `dotnet Api.dll` 自架 Kestrel 監聽（`verify-integration.py:19,36`），完全繞過 IIS，所以 web.config 內容對不對，這次 smoke 根本不會被觸發。
- **環境變數與 config 讀取方式相同**：`Program.cs` 沒有讀 `appsettings.json`（沒有 `builder.Configuration.Get...` 之類呼叫），只讀 `OC_RUN_DIR`、`OC_FAULTS`、`OC_SINK_URL`/`ASPNETCORE_URLS`（`Program.cs:10,14` 及 `verify-integration.py:19`），這些都由 script 統一注入，跟 build/publish 無關。

## 2. `package-manifest.json` 的 SHA256 能證明什麼

**能證明**：清單裡列的每個檔案，在「產生 manifest 當下」的內容雜湊值是什麼；可用來事後比對這些檔案有沒有被搬動、複製、傳輸過程中損毀或被竄改。

**不能證明「這次 smoke 測的就是這一包」整體**，只能證明其中一個檔案：
- `runs/package-smoke-01/report.json:188` 的 `artifact_sha256` 是 `37cd28507e95aa6e8f7ef1c7d9a0530aed0cfa9c0215a4f8e6bc7eeaefc516eb`，跟 `package-manifest.json:3` 裡 `Api.dll` 的雜湊完全一致 —— 這確實證明了**這次啟動用的 Api.dll，就是 manifest 記錄的那個 Api.dll**。
- 但 `report.json` 只 hash 了單一檔案 `exe`（見 `verify-integration.py:69` 的 `hashlib.sha256(exe.read_bytes())...`），沒有對 `Domain.dll`、`Api.deps.json`、`Api.runtimeconfig.json`、`VERSION`、`web.config` 做交叉核對。換句話說，manifest 上另外 8 個檔案是不是這次實際被載入使用的那份，**沒有任何紀錄佐證**。
- manifest 本身沒有時間戳記、沒有對應的來源 commit/hash、沒有簽章，所以它只是「內容雜湊清單」，無法單獨證明產出的來源、產生時間，或防止事後被整組重新產生來配合被竄改的檔案（沒有防偽機制，只有比對機制）。

## 3. 這次 smoke 檢查跟之前整合驗證是同一組嗎

**是同一組，且是同一支腳本**。`verify-integration.py` 裡 `--artifact` 只影響是否執行 build 步驟和 exe 路徑（`verify-integration.py:20,32-35`），實際的檢查邏輯（下單、四種 cancel 情境、401、三個 state 查詢、通知 payload、log 內容，共 10 類 check，`verify-integration.py:44-60`）完全沒有分支，兩種模式跑的是逐字相同的斷言。

所以這次多證明的是：**「dotnet publish 出來的產物，用 `dotnet Api.dll` 直接跑起來，在這組既有的 happy-path／錯誤路徑測試下，行為跟從原始碼重建後的行為一致」**——也就是驗證了「打包過程本身沒有破壞這幾條已知路徑的行為」，而不是新增了任何測試覆蓋範圍。如果只是照抄同一組檢查重跑一次，沒有針對「發布特有」的風險（見下題）加任何斷言，那就只是重跑，不是加深驗證。

## 4. 「原始碼會過、產物不會過」但這次 smoke 驗不出來的錯誤

- **VERSION 檔案沒被正確複製到發布目錄**：`Program.cs:12-13` 邏輯是「VERSION 存在就讀它，不存在就退回 `OC_VERSION` 環境變數或 `"unknown"`」——是靜默 fallback，不會丟例外。而 `verify-integration.py` 的所有 check 都沒有斷言 `version` 欄位（`/health`、`/ready`、log 裡都有 `version`，但 check 清單裡完全沒人檢查它，見 `verify-integration.py:44-60`）。所以就算 publish 漏帶 VERSION、版本號錯亂，這次 smoke 會全綠通過。要驗到，需要額外斷言 `/health` 或 `/ready` 回傳的 `version` 等於預期值。
- **web.config／IIS 託管設定錯誤**：manifest 有列 `web.config`（`package-manifest.json:11`），但整個 smoke 流程是直接 `dotnet Api.dll` 起 Kestrel（`verify-integration.py:36`），完全不經過 IIS/ANCM。若 `web.config` 裡的 `processPath`、`hostingModel` 設錯，導致「在真正的 IIS 環境下」啟動失敗，這次 smoke 完全測不到，因為它根本沒用到這個檔案。要驗到，得改成用 IIS Express 或實際 ANCM 環境啟動並打相同的 HTTP 檢查。
- **執行目錄相依的路徑假設**：`verify-integration.py:36` 不論 `--artifact` 與否，`cwd` 都固定是 `ROOT`（原始碼倉庫根目錄），不是產物實際部署的資料夾。如果將來程式改成用相對路徑（相對於 `cwd` 而非 `AppContext.BaseDirectory`）去讀某個檔案，在「cwd=ROOT」這個測試場景下不會出錯，但换到正式環境（cwd＝部署目錄，可能沒有 `src/` 或 `VERSION` 之外的原始碼結構）就會出錯——這次 smoke 因為 cwd 沒換成 artifact 目錄，驗不出這類差異。
- **framework-dependent 部署缺少對應 shared runtime**：`Api.csproj` 沒指定 `RuntimeIdentifier`/`SelfContained`（`src/Api/Api.csproj:2`），代表這是 framework-dependent 發布，執行機器需要另外裝對應版本的 .NET 執行環境。目前 smoke 是在**同一台機器**上跑 build 版和 artifact 版，兩者共用同一個本機已安裝的 runtime，所以「目標主機沒裝對應 runtime」這種部署環境差異，這次 smoke 天生驗不到（不是流程設計疏漏，而是同機測試的本質限制）。

---

### 來源 vs. 推論

**從檔案直接讀到的事實**：
- `verify-integration.py` 兩種模式都用 `dotnet <exe>` 啟動，從未呼叫 `dotnet run`（`verify-integration.py:36`）。
- 無 `--artifact` 時執行 `dotnet build`（Debug 預設），取用 `bin/Debug/net9.0/Api.dll`（`verify-integration.py:20,33`）。
- 兩種模式 `cwd` 皆為 `ROOT`（`verify-integration.py:36`）。
- `Api.csproj` 未設定 `Configuration`、`RuntimeIdentifier`、`SelfContained`，只設定 TargetFramework/Nullable/ImplicitUsings，並把根目錄 `VERSION` 複製進輸出（`src/Api/Api.csproj:1-4`）。
- `Program.cs:12` 用 `AppContext.BaseDirectory` 讀 VERSION，讀不到則 fallback（`Program.cs:13`），且沒有任何 check 斷言 `version` 欄位（`verify-integration.py:44-60`）。
- `package-manifest.json` 只有檔名→SHA256 對照，沒有時間戳、來源、簽章欄位。
- `report.json` 的 `artifact_sha256` 與 manifest 裡 `Api.dll` 的雜湊完全相同（`runs/package-smoke-01/report.json:188` vs `package-manifest.json:3`），且只 hash 了 `exe` 這一個檔案（`verify-integration.py:69`）。
- checks 邏輯在有無 `--artifact` 下完全相同（同一段程式碼，無分支，`verify-integration.py:44-60`）。

**推論（依據不足、需標明）**：
- Debug/Release 兩種 build 在功能行為上「理論上」一致，因為沒看到 `#if DEBUG` 或 config 相關分支——但這只是「沒讀到反例」，不是驗證過兩份輸出位元組級一致；沒有實測資料佐證。
- web.config 內容正確與否是否真的只影響 IIS 場景——這是根據 ASP.NET Core Module 的一般行為推論，專案裡沒有 web.config 內容本身可讀（manifest 只給雜湊，沒給內容），所以無法確認它目前實際配置了什麼。
- 「目標部署機器可能缺少對應 shared runtime」是基於 csproj 沒設定 self-contained 的常規推論，專案裡沒有任何部署腳本或 CI 設定可佐證實際部署目標環境。