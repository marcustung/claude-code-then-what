# 查核結果契約 v1

此契約是Day19新增的教學介面，不是Day17歷史JSON格式。

必要欄位：schema_version=1；order_id、notification_id、version 與 task.json 相同；sender_status 與 receiver_status 只能 confirmed/unknown；evidence_refs 是字串陣列；missing_sources 是非空字串組成的陣列（已確認時可為空）；next_action 為非空文字。

confirmed 必須引用來源清單中對應 side/event，且三個識別欄位全部相符的紀錄。unknown 必須說明缺件與下一步。next_action 只是待審文字，不能當作可執行命令。

工具輸出的來源清單與任務由執行端保存，模型不能靠修改這兩份輸入或檢查器取得通過。本包是本機離線驗證，不實施OS寫入權限、來源簽章或查詢時間窗驗證。

## 可加入既有 Skill 的輸出要求（尚未模型實跑）

回傳本契約的 JSON。通知ID與版本取自任務，evidence_refs 只引用工具留下的來源編號。接收端無依據時保留 unknown，列出缺件與下一步。檢查失敗應補查或修正結論，不得修改任務、來源或檢查器來通過。缺工具就停在待查，不自行補送或結案。
