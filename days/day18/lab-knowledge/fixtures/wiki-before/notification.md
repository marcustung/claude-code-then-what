# 取消與通知

- 適用版本：delivery-hardening-local-r2。
- 整理方式：本次對照保存的程式與設計，由文章備稿核對；不是新的模型執行結果。
- 維護責任：教學包由作者維護；套到團隊時指定服務 Owner 確認設計與接受條件。

## 可核對的實作

API 呼叫 OrderStore.TryCancel；該方法在同一個 lock (_g) 內取得訂單、呼叫 Cancellation.Cancel 並寫回。這限定為同一程序、同一 store instance 的這段操作。來源：[Program.cs](../sources/Program.cs)，定位 OrderStore.TryCancel。

通知建立、Channel.WriteAsync 在 TryCancel 回傳後才進行，不在該 lock 裡。不能從上述保證推成「訂單與通知是同一筆持久化交易」或跨程序 exactly-once。來源：Program.cs 的 /orders/{id}/cancel 與 channel.Writer.WriteAsync。

正常非同步路徑：API → TryCancel → 建立 Notification → Channel → NotificationWorker → HTTP 接收端。故障注入 sync_notify 會改走同步 SendOnce；本筆正常觀測不能套到所有設定。

notify_sent 由 worker 在 HTTP 回應成功後寫入，只證明發送端觀察到成功。接收端 confirmed 另需相同 notification_id 的接收紀錄；沒有驗退款完成。來源：Program.cs 的 resp.IsSuccessStatusCode 與 notify_sent。

訂單與 Channel 存在記憶體；程序重啟不能以換回程式推定資料恢復。來源：OrderStore、Channel.CreateUnbounded。

## 未取得的決策

來源沒有提供公司 SLA、正式接收端、補送授權或真人值班 Owner，均不可補寫。程式呈現實作，不能代替業務確認這就是想要的行為。
