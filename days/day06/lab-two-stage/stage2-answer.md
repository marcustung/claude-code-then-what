# 驗收草稿 v2（僅整理，未實作、未執行測試）

## 需求來源與版本
- `spec.md`：`SYNTHETIC spec v1`（公開合成教學題目，非公司實際政策，spec.md:5）
- `decision.md`：`DEMO-DECISION-01`（**純教學假設決策，非公司政策、非真實 Owner 核准**）
- `previous-draft.md`：前版驗收草稿，作為本次修訂基準

## 本次新增決策內容（DEMO-DECISION-01）
適用範圍：**已付款（Paid=true）、未出貨（Shipped=false）、尚未取消（Cancelled=false）** 的訂單。

決策內容：
1. 取消功能只將 `Cancelled` 設為 `true`
2. `RefundRequested` 固定回傳 `false`（退款交由另一流程決定，本功能不處理）
3. 不得呼叫付款服務（呼應 LIMIT-01，無新增例外）
4. 除此情境外，其他行為（已出貨取消、未付款取消、重複取消等）**仍未決，不代答**

> 再次強調：此決策為教學示範用途，用於示範「如何在未決問題中局部收斂驗收範圍」，並非真實業務規則核准。

## 具體驗收案例（Given/When/Then）

### 案例 A（新增，依 DEMO-DECISION-01）
- **Given** 訂單狀態為 `Shipped=false, Paid=true, Cancelled=false`
- **When** 使用者執行取消操作
- **Then**
  - 回傳 `CancellationResult.Order.Cancelled == true`
  - 回傳 `CancellationResult.RefundRequested == false`
  - 過程中未觸發任何付款服務呼叫、網路、檔案等副作用（LIMIT-01）

### 案例 B（沿用前稿，明示行為）
- **Given** 訂單狀態為 `Shipped=false`（付款狀態未指定）
- **When** 使用者執行取消操作
- **Then** 回傳的 `Order.Cancelled == true`（spec.md REQ-01 明示允許取消未出貨訂單）

## 相對前稿的變更
| 項目 | 前稿 | 本稿 |
|---|---|---|
| 未付款狀態下的 `RefundRequested` 規則（問題 2） | 待確認 | **已由 DEMO-DECISION-01 局部收斂**：僅針對「已付款、未出貨、未取消」情境，`RefundRequested` 固定為 `false` |
| 是否呼叫付款服務 | 屬 LIMIT-01 一般限制 | 決策重申此情境下不得呼叫付款服務，無新增例外 |
| 驗收案例 | 僅 1 個明示情境 | 新增案例 A，共 2 個明示情境 |
| 適用範圍界定 | 未區分 Paid/Cancelled 狀態 | 新增決策明確限定於 `Paid=true, Shipped=false, Cancelled=false` 這一狀態組合 |

## 仍未決事項（沿用前稿，未被本次決策涵蓋）
1. 已出貨訂單（`Shipped=true`）取消時的行為與是否需要 Success/Error 欄位
2. 已付款訂單取消**成功後**，若非「未取消」初始狀態（如重複取消）的 `RefundRequested` 規則
3. 未付款（`Paid=false`）訂單取消時 `RefundRequested` 應為何值
4. 已取消訂單重複取消是否冪等
5. `Order` 為 null / 非法狀態組合（如 `Shipped=true, Paid=false`）的處理
6. 回傳 `Order` 是否需為新物件（immutable）
7. 實際方法簽章、參數順序、靜態/實例方法

## 建議確認角色（沿用前稿）
- **Product Owner**：確認問題 1、2、3、4（業務規則）
- **Tech Lead**：確認問題 5、6、7（技術介面設計）

## 受阻範圍
- 除 DEMO-DECISION-01 已收斂的單一狀態組合外，其餘 7 項未決事項仍**無法**實作或撰寫對應測試
- 本草稿僅完成新增決策的整理與案例補充，**未修改、未實作、未執行任何程式或測試**，且**未主張任何真實 Owner 已核准**上述規則