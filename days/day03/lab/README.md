# 訂單取消：Day 3 公開合成案例

2026-09-15，一次 Claude CLI 呼叫，無工具、safe-mode、strict MCP、sonnet alias、low effort。原始回覆見 response.txt，輸入見 prompt.txt，事前判準見 protocol.md。介面含 Paid／RefundRequested，會引導退款聯想，不能宣稱模型憑空新增退款領域。

實際輸出：未出貨且尚未取消的訂單轉為取消；已付款則 RefundRequested=true。只設定記憶體旗標，沒有付款服務或退款交易。模型有列退款假設及待確認問題，非隱藏決策。

Codex 檢視 source 後執行模型原樣測試：7 組情境、18 個斷言全過，exit 0。程式及測試與 answer.json 原樣相符。依事前兩個需求條件檢視：已出貨不新增取消、未出貨可取消，與實作及測試吻合；未新增獨立測試套件，不能稱獨立完整驗收。退款預期為模型自訂，通過不能授予業務許可。

環境：首次 net8 編譯後因缺 runtime 無法執行，接著 net10 因 SDK 不支援失敗，最終以 net9 執行成功；兩次環境失敗皆保存，未修改模型程式或重抽模型答案。

重跑：在本目錄執行 `dotnet run --project Demo.csproj`，需要 .NET 9 SDK/runtime。僅本機原件，尚未發布公開 repo；不宣稱成效或一般模型出錯率。
