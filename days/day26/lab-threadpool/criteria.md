# ThreadPool 小型實驗事前條件

- 目的：評估教學案例能否支持 Day26 的症狀、阻塞位置、修法、同负載驗證；不是重建歷史公司事故。
- 同一訂單 API/Domain/FakeSink 副本。唯一区別：500ms 模擬查詢以 GetAwaiter().GetResult() 或 await 等待。
- 各次使用新程序、同一 Release 組件，384 筆不同訂單、96 個併發客戶端，每張取消一次；本機閉迴路固定數量負載，並非 production capacity。
- DOTNET_PROCESSOR_COUNT=2 讓兩組 runtime 使用相同處理器提示，非 OS CPU 配額；不設定 ThreadPool 最小或最大值，不限制 heap。
- 順序 blocking/async/async/blocking，降低順序偏差；各程序先跑3筆取消暖機。量測與堆疊擷取分開，避免暫停取樣影響計時比較。
- 判定：不能只看 p95；需同時觀察 pending、thread count、工作完成速率，並由獨立 diagnostic run 擷取到同步等待堆疊。若未捕捉則寫未證實。
- 改善：兩次 await p95 都應低於兩次 blocking；所有384請求成功，訂單狀態與獨立接收端 order_id 一一對上，沒有重複。
- 功能回歸：重複取消不再轉換、不再通知；已出貨409、未授權401、不存在404、已付款取消保留退款旗標。
- 安全：僅 loopback、每次新資料、請求30秒逾時、單輪120秒上限；關閉的只限本腳本啟動的程序。
- 本階段由 Codex 建立並執行，不呼叫 Claude，不宣稱已測得 Claude 診斷能力。原 OOM 成稿與原件不改。
