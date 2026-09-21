# 答案卷 v1（故意保留當年的錯答，供實驗比對；Claude 不會讀到這份）

症狀 1（計薪端提前累計）：`Payroll/MonthlyTaxCalculator.cs` 期間結束日取起日加天數，得到期末日的下一天，再用 `<=` 比較，端點多含一天。→ 正確。
症狀 2（報表人數提前累計）：報表走 `DependentRepository.ListEffectiveInPeriod`（有日期條件，SQL 正確），問題在呼叫端傳入的期間，往呼叫端追。→ **這格是錯的**：報表實際走 `ListForPayrollGroup`，沒有日期條件；計數也不看日期。
兩個症狀共用過濾邏輯：是。→ **錯**：只共用主檔，不共用任何過濾程式碼。
