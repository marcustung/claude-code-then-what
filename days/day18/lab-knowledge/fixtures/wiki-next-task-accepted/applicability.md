# 通知結論的使用條件

適用：delivery-hardening-local-r2 教學程式，非正式維運授權。由作者依 sources/Program.cs 與 Cancellation.cs 核對整理。

| 結論 | 使用條件 | 不能推出 | 何時重查 | 下一步 |
|---|---|---|---|---|
| notify_sent 表示發送端見到 HTTP 成功 | 對照程式的 IsSuccessStatusCode；確認本次版本及 sync_notify 設定 | 接收端業務完成、使用者已收到、需要補送 | 成功判斷、呼叫路徑、接收端契約變更 | 相同 notification_id 查接收端接收及處理紀錄 |
| 成功紀錄不只來自背景 worker | 非同步 ExecuteAsync 與 sync_notify 的 SendOnce 都會記 notify_sent，後者帶 sync=true | worker 沒查到就一定沒送出 | 通知模式或記錄點改變 | 有 sync=true 時核對 SendOnce，並核對當次設定來源 |
| 重複取消不是補送入口 | Cancellation.Cancel 與 API 的 Transitioned 分支；已取消時不再建通知 | 可以再呼叫取消補通知 | 冪等邏輯、通知建立條件改變 | 先確認接收端狀態與獨立補送方法 |

來源：[API 與通知](../sources/Program.cs)、[取消規則](../sources/Cancellation.cs)。Wiki 敘述須再核對來源；案例中的環境標示不是部署證明。

## 缺件與決策

沒有接收端證據就保留送達未知，不等於沒送達。不知道補送契約就不能建立補送授權。本教學案未提供補送 API、接收端去重契約或指定 Owner，應提出缺件與需確認角色，不能編人名。

服務維護者確認查詢來源與部署版本；有權接受重複副作用風險的人確認補送條件。這是建議分工，不是公司已採用規範。
