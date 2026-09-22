# Day 9：訂單取消開工分析

目的：對照需求、v1程式與測試，留下修改範圍，再進設計。不是完整服務、不是部署範例。

## 不呼叫模型，先查已保存的證據
需求：Python 3（只用標準函式庫）。在本資料夾執行：

```sh
python verify.py
```

輸出 JSON：六個輸入雜湊是否一致、八組布林旗標表達是否等價、兩輪工具是否限於 Read/Grep/Glob 以及是否交回結果。退出碼0代表這些機械檢查通過，不代表分析語意全對。

再讀 runs/r1/result.md、runs/r2/result.md、scope-handoff.md。核對第二輪如何更正第一輪的全域斷言，及 Codex 如何修正「必須固定判斷順序」的過度要求。

## 自己再跑（會消耗 Claude 用量）
需已安裝並登入 Claude Code；驗證本機 `claude --help` 支援所用參數。runner 優先搜尋 PATH 的 claude.exe 或 claude，找不到時才查 ~/.local/bin。

```sh
python run.py my-reader-run reader
python run.py my-original-run r1
python run.py my-source-review r2
```

第三個命令沿用保存的第一輪報告做來源補件演示，不是自動銜接 my-original-run。需改實驗對象時請另存提示與來源。每次使用新目錄；既有結果不覆寫。

safe mode 關閉使用者自訂但管理政策仍可能生效。工具清單限 Read/Grep/Glob；不是作業系統隔離。原始 trace 可能包含本機路徑，對外分享前請去識別。

## 材料
- manifest.json：原始來源與 SHA256；只聲明指定六個輸入，不涵蓋完整服務。
- packet-context.md：第二輪新增來源說明。
- prompt.txt／prompt-r2.txt：兩輪不同提示；非A/B。
- runs/r1、runs/r2：原始 trace、提示、輸出與 metadata。
- scope-handoff.md：Codex 覆核後交接稿，沒有 Owner 接受。
- verification.json：verify.py 的保存輸出。

原始 Day 9 理由 A/B 與本次是不同案例，不借用其分數。教學的退款旗標不是實際退款。


## 旗標條件的補充核對

但它的第二輪報告又往前走了一步，要求「先判斷已取消，再判斷付款」。這是一種可行寫法，卻不該被升格成唯一規格。以本範例的三個布林欄位來說，退款要求也可以表達成：

```csharp
bool shouldRequestRefund =
    !order.Shipped && !order.Cancelled && order.Paid;
```

這段是核對規則用的等價條件示意，不是已套用的修復。它只回答退款要求旗標，不涵蓋訂單狀態更新、例外或外部服務。

Codex 另外用小程式列舉三個布林值的八種組合，核對「提前返回」與「組合條件」兩種寫法的旗標結果相同。這個檢查支持的是兩種表達可以等價，不能代替之後的 .NET 功能測試。

**Claude 幫忙找到規則交會的風險；交給設計者的，應該是要保住的行為與反例，不能把某種寫法直接當成業務要求。**

第一輪版本混用的原句見 `runs/r1/result.md` 第63行。第二輪未逐項撤回這項說法，Codex覆核後才從交接結論排除，不能寫成Claude自行修正了所有問題。

## 讀者提示實跑

`reader-prompt.txt` 是正文提示代入本包路徑的版本。`reader-01` 是調整前，`reader-02` 是目前版本。兩次在不含歷史回答的乾淨資料夾執行，沒有修改來源。

- reader-01 把 record 的值與身分混用，誤稱 SC-06 也會失敗。
- reader-02 逐欄承認 SC-06 值符合、SC-07 退款旗標不符，但仍過度限定分支，且誤稱通知決策全列 proposed。
- 採用依據與拒絕理由見 reader-audit.md；機械 verifier 不判斷自然語言正確性。

`verify.py` 不呼叫模型；`run.py` 會呼叫已登入的 Claude Code 並產生用量。模型回覆可能不同，完成紀錄不等於分析正確。
