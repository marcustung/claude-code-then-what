# 查詢知識

適用：Day17 本機 Grafana/Loki/Alloy 教學設定。服務版本相同，收集設定仍可能不同，兩者都要核對。

- 來源：[config.alloy](../sources/config.alloy)。
- 服務標籤是 service_name，不是 service。
- 發送端值 order-api，接收端值 notification-receiver。
- lab_case 區隔教學情境，order_id 與 notification_id 從 Log JSON 內容串接，不當成固定標籤。
- datasource、時間窗與本次事件看 task.json；不要把範例的一組 ID 固定寫進 Skill。
- 回傳零筆先核對標籤、服務與時間窗；工具錯誤與成功的空結果分開。

查不到接收紀錄只能留下 unknown，不能從 Wiki 宣告某筆通知送達。Wiki 提供查詢背景，本次結果仍要查本次資料。
