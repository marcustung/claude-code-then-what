# 合成規則 v2（Codex 為本 POC 固定的測試裁決，不是企業 Owner 決策）
R-01：待審申請可以進入面試中。
R-02：已拒絕申請不可直接回到面試中。
R-03：例外只在 Reopened 與 Authorized 均為 true、Role 為 HiringLead、Reason 非空白時允許。其他已拒絕申請維持禁止。已在面試中的申請不重複轉換。
Authorized 為本題給定的可信輸入；不宣稱完成真實身分或授權驗證。
