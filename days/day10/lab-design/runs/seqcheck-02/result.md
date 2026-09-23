逐箭頭核對結果：

1. `C->>A: POST /orders/id/cancel`（第48行）— 一致。
2. `A->>S: TryGet(id)` / `S-->>A: before`（第63行）— 一致，但圖漏掉了前面的 actor 檢查（第57–62行，缺 `X-Actor` 時回 401 並直接結束，不會走到 `TryGet`）。**圖不完整**，屬圖漏分支。
3. `A->>D: Cancel(before)`（第69行）— 一致。
4. `A->>D: Transitioned(before, result)`（第70行）— 一致。
5. `A->>S: Put(id, result.Order)`（第73行）— **順序不一致**：圖把 `Put` 畫在 `Transitioned` 回傳「true」之後單獨一步，但程式中 `Put` 只在 `before.Shipped` 為 false 且 `transitioned` 為 true 時才執行（第72–74行的 if/else if/else 三分支）。圖只畫了「transitioned=true→Put」這一條分支，漏掉 `Shipped`（409，不 Put，不通知）與「未 transitioned」（idempotent，不 Put，不通知）兩個分支。**屬圖漏分支，非程式問題**。
6. `A-->>C: 200 {...}`（第89行）— 位置不一致：程式中 HTTP 回應（第89行）是在第86–88行（計算延遲、寫 log）之後才回，且是在通知 enqueue（第76–84行）**之後**才回應客戶端，並非圖中畫的「先回 200 給 Client，再 enqueue 通知」。**圖錯**：實際順序是先 enqueue／等待通知，才回 200，不是非同步並行先回應。
7. `A->>N: enqueue Notification`（第79、84行）— 對應程式碼存在，但如上所述，在程式裡此步驟發生在回應 Client（第89行）**之前**，圖畫反了順序。此外，若 `faults.SyncNotify` 為真（第81–82行），走的是同步呼叫 `NotificationWorker.SendOnce`，並非圖中所畫的走 channel 交給 `NotificationWorker`／非同步 `enqueue`；圖僅涵蓋了 `else` 分支（第84行）的非同步路徑，屬程式分支未在圖中呈現。
8. `N->>K: POST /notify` / `K-->>N: 200`（NotificationWorker 內部，不在此檔案 48–92 行範圍內）— 無法由此兩個檔案核對，需檢查 `NotificationWorker` 原始碼確認。

## 結論摘要
- **圖漏分支**：缺 401 unauthorized（57–62行）、404 not_found（63–68行）、409 rejected_shipped（72行）、200 idempotent（74行）四種不通知/不 Put 的情況；圖只畫了唯一的 happy path（transitioned=true）。
- **圖錯（順序顛倒）**：回應 Client（第89行）實際發生在 enqueue 通知（第76–84行）與寫 log（第88行）**之後**，圖卻畫成先回應 Client 再 enqueue，暗示回應與通知是並行/非同步不影響回應時間，但同步模式（`faults.SyncNotify`=true 時，第81–82行）下通知會阻塞在回應之前完成，這點圖完全沒表現。