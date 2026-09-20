# Day 4 本機 POC 驗證結果

日期：2026-09-13（Asia/Taipei）。.NET SDK 9.0.314；Claude Code 2.1.269。模型要求 sonnet、low effort；實際模型用量欄位見原始 JSON。本機 Claude CLI 純文字審查，不是 Claude Code Action。

## .NET 實際結果

| 檢查 | 結果 | 能說明什麼 |
|---|---|---|
| Release build，警告視為錯誤 | exit 0 | 此專案成功編譯與啟用的分析器檢查 |
| 第一版＋原作者假設案例 | 6/6 通過 | 測試可以與未確認的例外假設一致 |
| 第一版＋固定 v2 驗收 | 6/10 通過，4 失敗 | 無角色、錯誤角色、無理由、空白理由仍被允許 |
| 第二版＋同一組 v2 驗收 | 10/10 通過 | 此小範圍修改符合固定案例 |

使用 .NET console 斷言 runner 與 exit code，不是 dotnet test、不是 GitHub CI 實跑。原始紀錄、起訖與 SHA-256 見 [manifest](results/manifest.json)。每組案例的輸入與預期值在 Program.cs。

## Claude 審查

乾淨設定、隔離兩版方法的 [v1 原文](results/review-v1.md) 指出新增重開例外缺乏規則依據，沒有假稱測試已跑。這是有明顯提示的教學題：v1 規格明寫「未定義」，不能估算真實缺陷檢出率。

[v2 原文](results/review-v2.md) 保留完整發現與限制，不能把 CLI exit 0 當成模型核准。審查輸入只附規格與目標方法，沒有附 runner 與執行紀錄；模型指出缺測試材料是這次輸入限制，不代表本機沒有測試。

v1 審查把「未定義授權角色」延伸成應綁定角色的規則精神，部分措辭超過原規格能證明的範圍；只能採納為待裁決問題，不能全數當已證實缺陷。

第二版審查把 Interviewing 沒有顯式分支列為缺件；但布林條件已回傳 false，固定案例亦通過。這是可讀性建議與回傳語意待釐清，不能升格為已證實的邏輯缺陷。報告中的「不核准」是模型文字，沒有任何 GitHub 審查或阻擋效力。

## 保留的無效與探索紀錄

- results/pilot-both-methods：初輪同時提供兩版方法，存在答案提示，不用作獨立比較。
- results/pilot-isolated-context：隔離方法後，v1 僅輸出讀取個人知識庫的工具呼叫文字，未完成審查；exit 0 不代表交付完整。v2 有審查輸出，仍保留原樣。
- results/review-v1、v2：改用空設定來源及純文字 system prompt 後，兩版重新執行；工具清單為空，不讀外部檔案。

共三組、六次模型呼叫，沒有只保留成功輸出。第二版規則與實作在所有模型審查前已固定，由 Codex 為合成題編寫，不是收到 Claude 意見後才修的歷史時序，也沒有真人 Domain Owner 裁決。

## 尚未驗證

Claude Code Action 認證／觸發／PR 脈絡、遠端 CI、CODEOWNERS 真實帳號、必要審查、bypass 與新 commit 後核准失效均未驗證。使用者指定先完成本機驗證。現有 workflow 是準備檔，Owner 為占位符，不宣稱會實際攔截。

本題只測允許轉換的純函式，Authorized 是給定輸入，不含身分驗證、資料寫入、並行或真實權限。未測人工 Loading、誤報率或整體效率。沒有新增 PR 或向他人發訊息。

重跑：在本目錄執行 node run.cjs。run.cjs 把中間的 4 個失敗視為預期反例，但保留該次程序 exit 1；最終 runner 只有在 exit 序列為 0,0,1,0 時成功。
