# 合成前後行為

原規則：Pending → Interviewing；Rejected → Interviewing 禁止。
第一版：Rejected 加入 Reopened && Authorized 例外，無角色／理由依據。
第二版：只在 v2/R-03 所有條件成立時開放；其他維持禁止。
此為純函式 POC，未涵蓋資料寫入、並行或權限來源。
