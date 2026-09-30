# Day15 上 Production 前的壓測計畫

目標：以同一發布包核對尖峰及短時持續負載下取消行為、通知完整性與延遲。不是 Production 部署、SLA 或容量保證。
版本：../runs/candidate-checked/package；執行前後核對十檔 SHA-256。
環境：Windows 單機 .NET9，loopback API，假接收端200；Prometheus/Grafana 為獨立本機容器。沒有 Production 流量資料。
需求來源：教學規格防止重複取消副作用；p95<250ms、HTTP失敗0、checks=100%、dropped_iterations=0 都是本輪事前教學門檻。PM/SRE/Owner 未簽核，不當公司標準。
工作：每次建立已付款未出貨訂單→取消→重送取消→查狀態。每迭代四次HTTP，不把迭代率當RPS。通知完成後以ID對帳，不進metric標籤。
負載：smoke 1次迭代/秒20秒；spike 2/s 20秒→20/s 30秒→2/s 20秒；sustain 10/s 120秒。均為constant-arrival-rate，各獨立啟動程序；不是長時間soak。
停止：腳本timeout整輪180秒、服務退出、錯誤率>5%持續評估（起始10秒後abortOnFail）、通知排空20秒仍不齊則判失敗。模式未明拒跑。
架構（待Claude核對程式）：API→OrderStore.TryCancel全域鎖→Domain→Channel→NotificationWorker→FakeSink；回應前入列，送達不固定先後。請核對圖與程式差異，勿僅憑圖下根因。
量測：k6 latency/error/checks/dropped；程序/metrics queue/working set/heap/GC；原始通知收據。CPU如未提供不編造。Memory內訂單增加不是直接等於leak。
決策：先驗實驗是否可用；不達門檻查原因。即使通過，auth、durability、backup、環境差異仍未驗，不准正式上線。後續才從線上issue重現與修法出發。
