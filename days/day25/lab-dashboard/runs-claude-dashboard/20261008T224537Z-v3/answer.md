我現在還沒辦法開始建立第三版。每一次執行 `gcx` 指令(連 `gcx --help` 也一樣)都需要你核准,而核准都沒有通過。所以我到現在還沒看過任何實際資料。

目前已經做的:
- 讀完 `notification-contract.md` 和 `previous-version.json`。
- 還沒建立任何 Dashboard,也沒寫 `dashboard.json`,更沒動到其他 Dashboard。

接下來需要資料,才能做第三版:
- 這些指標的實際內容:`work_status`(輪次、結論、原因)、`work_stage_count`、`work_unmatched`。
- 資料裡「下一步」和「負責人」的欄位或標籤在哪裡。我不會自己猜或改寫。
- Loki 的 log 欄位,尤其是通知編號。

請你二選一:
1. 核准 `gcx` 指令(或把 `gcx` 加進這個目錄的 Bash 允許清單),我就繼續探索、建立、驗證每個面板的查詢,最後存成 `dashboard.json`。
2. 你自己執行探索指令,把輸出貼給我。

我打算先跑 `gcx --help`,再查 `work_status` 的標籤,以及 Loki 的 service_name 欄位。