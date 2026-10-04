# Day 21 Eval 結果（batch smoke，1 次）

| 案例 | 條件 | 次數 | 發送端對 | 接收端對 | 誤判已送達 | 契約通過 | 平均回合 | 平均秒 | 平均 US$ |
|---|---|---|---|---|---|---|---|---|---|
| decoy-receipt | none | 1 | 1/1 | 1/1 | 0/1 | 0/1 | 5.0 | 22.7 | 0.1 |

總費用 US$0.101；gate 錯誤碼：
- decoy-receipt／none／r0：RETURN_FOR_EVIDENCE ['UNKNOWN_SOURCE_REF', 'SENDER_EVIDENCE_REQUIRED']
