# ORD-142 v2｜取消尚未出貨的訂單（規則補完）

承 v1（`spec-v1.md`、`decisions-v1.md`）。v2 由訂單 Owner 於教學示範中確認；本檔是這張票唯一的規則來源。

## 業務規則（BR）

| 編號 | 規則 | 來源 | 對 v1 的影響 |
|---|---|---|---|
| BR-01 | 尚未出貨、尚未取消的訂單可以取消，回傳 `Cancelled=true` | v1 保留 | 不變 |
| BR-02 | 已出貨的訂單不可取消：維持原訂單、`Cancelled` 不變、不丟例外 | v1 保留 | 不變 |
| **BR-03（改）** | 已付款、尚未出貨的訂單取消時，**要**提出退款要求：`RefundRequested=true`；未付款則 `false` | Owner 推翻 v1 決定第 3 列 | 既有測試「已付款取消不要求退款」預期要反過來 |
| **BR-04（新）** | 已取消的訂單再次取消：維持原狀、`RefundRequested=false`、不丟例外 | 補 v1 待確認項 | 新增測試 |
| 限制 | 不連付款服務、不執行退款、`RefundRequested` 只是記憶體旗標；三個型別簽名不可改 | v1 保留 | hook 的擋點 |

## 驗收場景（SC，Given／When／Then）

| 編號 | 規則 | Given | When | Then |
|---|---|---|---|---|
| SC-01 | BR-01 | 未出貨、未付款、未取消 | Cancel | `Cancelled=true`、`RefundRequested=false` |
| SC-02 | BR-02 | 已出貨、未取消 | Cancel | 回傳原訂單（同一個 record 值）、不丟例外 |
| SC-03 | BR-03 | **已付款**、未出貨、未取消 | Cancel | `Cancelled=true`、**`RefundRequested=true`** |
| SC-04 | BR-03 | 未付款、未出貨、未取消 | Cancel | `RefundRequested=false` |
| SC-05 | BR-02 | 已出貨、**已付款** | Cancel | 原訂單、`RefundRequested=false` |
| SC-06 | BR-04 | 未出貨、**已取消**、未付款 | Cancel | 原訂單、`RefundRequested=false`、不丟例外 |
| SC-07 | BR-04 | 未出貨、已取消、**已付款** | Cancel | 原訂單、`RefundRequested=false`（不重複退款） |

## 追溯（成稿時填）

BR → SC → `tests/Program.cs` 測試名 → `src/Cancellation.cs` 行 → PR → 結果
