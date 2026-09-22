# 驗收草稿（僅整理，未實作）

## 需求來源與版本
- 檔案：`spec.md`，標示為 `SYNTHETIC spec v1`
- 性質：公開合成教學題目，非公司實際政策（spec.md:5）

## 已明示行為（REQ-01 / 介面 / 限制）
- **REQ-01**：允許使用者取消「尚未出貨」的訂單。
- **介面定義**：
  - `Order(bool Shipped, bool Paid, bool Cancelled)`
  - `CancellationResult(Order Order, bool RefundRequested)`
- **LIMIT-01**：
  - 不得有外部依賴、網路、檔案、金流呼叫等副作用
  - `RefundRequested` 僅為記憶體內旗標，不觸發實際退款

### 明示的具體情境
- 訂單 `Shipped = false` → 可取消（明確允許）
- 輸出需回傳 `CancellationResult`，內含更新後的 `Order` 與 `RefundRequested` 旗標

## 未明示但會影響實作或驗收的問題（待確認，不代答）
1. **已出貨訂單（Shipped = true）取消時的行為**
   - 應回傳失敗/錯誤，還是回傳原訂單且 `Cancelled` 維持 `false`？
   - 是否需要額外的成功/失敗欄位（目前介面沒有 bool Success 或 error 類型）？
2. **`Paid` 與 `RefundRequested` 的關聯規則**
   - 若 `Paid = true` 且成功取消，`RefundRequested` 是否應設為 `true`？
   - 若 `Paid = false`，取消時 `RefundRequested` 應為 `false` 還是不設定？
3. **已取消訂單（Cancelled = true）重複取消的行為**
   - 是否視為冪等操作（回傳相同結果）還是應視為錯誤/例外？
4. **輸入驗證與例外情境**
   - `Order` 為 `null`/未初始化時的預期行為（介面未定義是否可為 null）
   - 是否有其他非法狀態組合（例如 `Shipped=true, Paid=false`）需特殊處理？
5. **回傳的 `Order` 是否為新物件還是原物件的變更**
   - 介面未說明是否需不可變（immutable）處理，會影響實作與測試中物件同一性的判斷方式。
6. **函式簽章/方法名稱**
   - spec 僅給出型別介面，未定義實際方法名稱、參數順序、是否為靜態方法等，需前對齊避免驗收時對不上介面。

## 建議確認角色
- **需求/產品負責人（Product Owner）**：確認問題 1、2、3（業務規則：出貨後取消策略、退款旗標邏輯、重複取消語意）
- **技術負責人 / Tech Lead**：確認問題 4、5、6（技術介面設計、null 處理、不可變性、方法簽章）

## 確認後的驗證方式（待雙方確認規則後執行，目前不執行）
- 針對每個明示情境（`Shipped=false` 可取消）撰寫單元測試驗證 `Cancelled` 被設為 `true`
- 針對確認後的未出貨/已出貨、已付款/未付款、已取消/未取消等狀態組合，建立測試矩陣逐一驗證 `Cancelled` 與 `RefundRequested` 結果
- 驗證過程中不得引入網路、檔案、金流等外部呼叫（符合 LIMIT-01），可用純記憶體物件斷言驗證

## 受阻範圍
- 因 6 項需求細節未明示，目前**無法**進行以下工作：
  - 完整實作 `CancellationResult` 產生邏輯（尤其是已出貨、重複取消、付款狀態下的分支邏輯）
  - 撰寫涵蓋所有狀態組合的驗收測試案例
  - 定義最終方法簽章與呼叫方式
- 本草稿僅完成需求盤點與問題整理，**未修改、未實作、未執行任何程式或測試**。