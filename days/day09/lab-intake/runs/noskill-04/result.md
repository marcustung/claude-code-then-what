讀完 spec.md 與現有 `src`/`tests` 後，找到了與這次「取消需求」直接相關的落差。以下只針對此次範圍(已付款取消時提出退款要求)提出，不做全系統審計。

## 核心落差

`spec.md:4` 要求「已付款取消時提出退款要求」，但 `src/Domain/Cancellation.cs:21` 目前寫死 `RefundRequested: false`，且 line 17 的註解也明確寫著「不提出退款要求」——這是與新 spec 直接衝突的舊行為，需要修正。

## 要改的檔案與行號

**`src/Domain/Cancellation.cs`**

- **第 17 行**:註解「已付款、尚未出貨的訂單取消後，不提出退款要求（decisions.md 第3列）」已過時,需改寫成描述新規則(已付款→要求退款),並改引用 `spec.md` ORD-142,不要再引用 `decisions.md`——這個檔案在本 repo 中根本不存在,不應被當作依據(呼應 spec.md 第7行的警語)。
- **第 21 行**:`return new CancellationResult(cancelledOrder, RefundRequested: false);` 改為 `return new CancellationResult(cancelledOrder, RefundRequested: order.Paid);`
  - 這是唯一需要的邏輯變更,符合 spec.md 第5行「只調整取消結果旗標、保留既有型別簽名」的範圍限制。
  - 第11–14行(已出貨guard)與第6–9行的方法簽名都不需要動。
- **第18–19行的註解**(「已取消的訂單再次取消屬未確認行為…不應據此撰寫測試預期」)可以保留,但建議補一句提醒:目前這行改動後,重複取消一個「已付款」訂單時,`RefundRequested` 也會是 `order.Paid`(因為程式沒有另外判斷 `order.Cancelled`)。這正好落在 spec.md 第6行「重複取消應回傳什麼？」的未決問題上,**建議先跟PM/Owner確認,不要自行決定**,程式本身不用為此加分支(超出本次範圍),但要讓下一個接手者知道這個副作用存在。

**`src/Api/Program.cs`**:不需要改。第79、88、89行本來就是原封不動轉傳 `result.RefundRequested`,domain層改完後這裡自動吃到新值,不用碰。

## 測試要改/新增

**`tests/DomainTests/Program.cs`**

- **第13行(v1-3)**:目前斷言「已付款取消不要求退款」(`!r.RefundRequested`),這是舊行為,與新 spec 相反,必須改成斷言 `r.RefundRequested == true`,測試名稱也要改(例如「已付款取消要求退款」)。
- **新增一筆**:未付款、未出貨取消 → `RefundRequested == false`。目前沒有任何一筆測試涵蓋「未付款」情境下退款旗標的值,改動後應該補上,避免以後又被改壞。
- **新增一筆**:已出貨且已付款 → 訂單不變、`RefundRequested == false`。確認 guard 分支(shipped)不受這次改動影響,因為它是提早 return,理論上不會被牽連,但這是最容易被回歸破壞的邊界,值得補一筆。
- **不要新增**:重複取消(已取消訂單再次取消)搭配已付款情境的退款斷言。spec.md 第6行明確列為未決,寫死一個預期值等於幫PM做了未經確認的決定。

## 給RD的提醒

1. `decisions.md` 這個檔案在本 repo 中不存在——`Cancellation.cs` 裡多處註解引用它,屬於前一輪練習留下的殘留引用,這次順手更新第17行時建議一併處理,但不用大改其他行。
2. 重複取消與併發取消(spec.md 第6行的兩個未決問題)不在本次範圍,程式與測試都不用處理,但建議在PR描述或後續task中明確記錄「這次沒有處理」,避免下一個人誤以為已經涵蓋。

以上為變更清單,未做任何程式修改、未執行測試,等你確認後再動手。