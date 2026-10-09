# Day26 ThreadPool starvation 小型實驗與 OOM 選題比較

> 後續已完成 Claude 獨立查因、兩版修法與回歸。最新採用判斷見 [驗證報告](CLAUDE-VERIFICATION.md)。以下保留初始小型實驗當時的比較與限制。

## 初始實驗結論

建議將 ThreadPool starvation 作為 Day26 的優先替換候選：本次已重現「CPU 不忙、記憶體不大，請求卻卡住」，並取得同步等待堆疊、同負載 await 對照與功能回歸。最有價值的發現是：客戶端沒有拿到成功，服務仍完成了取消與通知，能自然接到 後續 的安全重試。

但現在可直接發布的完整 Claude 案例仍是既有 OOM。這次是 Codex 設計與執行的受控教學測試，尚未讓 Claude 獨立調查或提出修法，不能冒充模型破案。原正文與封面不變。若補上隱藏故障答案的 Claude 查詢、堆疊查證與修復紀錄後仍成立，再替換 Day26；若沒有這一輪，保留 OOM。

## 來源與界線

- 沿用 `day26-live-lab/service` 的 .NET 訂單 Api、Domain、FakeSink，原始碼 SHA-256 存於 source-manifest.json，驗證原件未變。
- 在新的教學副本新增500ms `Task.Delay` 模擬外部查詢。這不是真實資料庫或 HTTP 下游，不是當年公司事故重建。
- 同一個 Release 組件以 LAB_WAIT_MODE 切換同步等待／await 路徑，其餘程式一致。這是修法的受控對照，不是 Claude 修改前後的組件。
- SDK9.0.314，實際 runtime 清單見 environment.json。DOTNET_PROCESSOR_COUNT=2 是 runtime 處理器提示，不是限制 OS CPU 為兩核心；沒有更改 ThreadPool 最小／最大執行緒，沒有縮小 heap。
- 同一台 Windows 同時跑客戶端、服務與接收端，屬本機小型教學負載，不能推估正式環境容量或普遍倍數。
- 每輪新程序；暖機3筆，正式384張不同訂單、96個併發工作者，每張取消一次，閉迴路固定數量測試。暖機另計，接收端總數387；負載訂單384逐筆核對。
- 順序 blocking → await → await → blocking。第5輪單獨擷取堆疊，不加入效能比較。
- 原版 RequestAudit 仍存在，但本次 body 只有空JSON；不把未發生 OOM 解釋成永久沒有記憶體問題。

## 事前判準

見 criteria.md。不能僅依 .Result/GetResult 字樣或延遲判定：需有執行緒／排隊趨勢、獨立堆疊，以及只改等待方式的對照。修後需維持訂單狀態、退款旗標、通知與正常拒絕行為。

## 實測結果

| 組別 | 384筆負載完成時間 | 客戶端終止等待 p95 | HTTP200 | 逾時 | 連線重設 | ThreadPool峰值 | pending峰值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 同步等待1 | 39.467秒 | 28.878秒 | 339 | 19 | 26 | 93 | 158 |
| await1 | 2.255秒 | 0.573秒 | 384 | 0 | 0 | 10 | 81 |
| await2 | 2.271秒 | 0.575秒 | 384 | 0 | 0 | 9 | 45 |
| 同步等待2 | 57.235秒 | 30.006秒 | 313 | 25 | 46 | 97 | 168 |

p95 是客戶端每次嘗試到收到回覆或例外的時間，包含30秒逾時上限，不能視為完整服務處理時間的p95。同步等待1/2的成功HTTP200請求p95另為約28.859/28.389秒。失敗不全是逾時；連線重設的底層機制本次未另外定位。

同步等待負載窗平均CPU消耗約單一核心的5.6%／3.3%；await為57.3%／49.3%。這是 TotalProcessorTime 相對實際時間差的取樣平均，非整台主機CPU百分比，兩組視窗長度不同。它支持故障期間CPU未飽和，不用來宣稱精確CPU效率改善。heap取樣峰值同步版11.2/12.4MiB、await8.7/7.4MiB，不像前案逼近縮小後的128MiB上限。

注意 await也有短暫pending，不能以單一queue峰值判故障。需要把負載時間線、thread count變化與實際阻塞堆疊一起看。

## 阻塞位置與修法

第5輪 `dotnet-stack report` 成功，6條堆疊包含：

```text
System.Threading.Tasks.Task.SpinThenBlockingWait(...)
...
Api!LabLookup.WaitSynchronously()
```

由 service/src/Api/Program.cs 可對回這段教學程式：

```csharp
public static async Task WaitAsynchronously() { await Task.Delay(500); }
public static void WaitSynchronously() {
    WaitAsynchronously().GetAwaiter().GetResult();
}
```

故障路徑在請求處理內同步等待非同步工作；對照路徑則 `await LabLookup.WaitAsynchronously()`，保持相同500ms模擬延遲。runtime在負載下增加執行緒，並非撞上最大執行緒上限；沒有用提高上限來遮住問題。延遲、排隊、執行緒與堆疊共同支持這個教學故障的ThreadPool starvation判斷，不推論當年的事故也是同一根因。

## 功能與最有價值的反差

兩次await各11項檢查全部通過：HTTP200、真正取消、退款旗標、訂單狀態、接收端逐筆order_id對帳、無重複通知、重複取消冪等、已出貨409、未授權401、不存在404、回歸操作沒有增加收據。

同步等待版雖有45/71筆客戶端失敗，收尾核對時384張負載訂單都已取消，接收端收到384筆各自對應通知，沒有重複。這份教學API沒有把客戶端中止傳入模擬等待，因此可以發生「客戶端放棄後服務仍完成」。不是所有服務都如此，卻是不能憑逾時就安全重送的具體示範。正式要寫後續仍須保留其獨立三情境驗證，不能把這裡當成安全補送已完成。

## 與 OOM 的比較

| 面向 | OOM現稿 | 本次ThreadPool案例 |
|---|---|---|
| 讀者進入 | 記憶體持續上升，很直覺 | async看似正確，CPU不忙卻卡住，有反差，但需解釋等待 |
| 調查深度 | heap、GC、Log、程式，沒有memory dump | runtime趨勢＋實際阻塞堆疊＋程式對照 |
| AI關聯實證 | Claude查詢、修改、重跑既有紀錄完整 | 尚無Claude實跑，目前由Codex設計與執行 |
| 管理判斷 | 保留紀錄與磁碟／隱私取捨 | 失敗回應與實際完成分開，重試風險 |
| 接後續 | 由修程式轉向是否可重試 | 這次就看見客戶端失敗但工作完成，接續更自然 |
| 立即發布 | 較完整 | 需补Claude獨立查因與修復，不宜冒充 |

故事潛力選ThreadPool；目前完整可發稿選OOM。建議先保存此實驗，下一個補強只做Claude獨立查因與修復，不同篇加入兩個完整事故。

## 證據與執行狀態

`runs/20261009T121013Z/` 保存四輪比較＋一輪堆疊；各輪含 requests.json、api/runtime.jsonl、api/logs.jsonl、sink/receipts.jsonl、summary.json。verification.json保存對帳、原始碼未改與堆疊檢查。summary.json為完整結果；environment.json紀錄runtime與限制。

五輪與程序清理完成後，收集環境資訊的 `dotnet --info` 在Windows workload installer失敗，導致runner最後退出1。實驗輸出已保存；改用 `--version`／`--list-runtimes` 補環境資訊並修runner metadata步驟，未重跑或覆盖原結果。不將整段runner退出狀態說成無錯誤。

本次未呼叫Claude、未使用公司資料、未修改Day26正文或封面、未對外發布。

## 參考

- Microsoft：Debug ThreadPool starvation：https://learn.microsoft.com/en-us/dotnet/core/diagnostics/debug-threadpool-starvation
- 官方方法也是結合慢請求、runtime counter、阻塞堆疊與程式；.NET6之後會對部分同步等待更快補執行緒，仍不代表同步等待沒有成本。
