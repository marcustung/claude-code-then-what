# 修訂紀錄

## 從舊設計結論到 r2 版本限定

原句：read/decide/write 非整體原子；個別 lock 不保證並行取消安全。

來源：sources/design-review.md 第 4 點。保留原件，不回寫歷史檔案。

新核對：r2 的 OrderStore.TryCancel 已在同一 lock 內取得、判斷並寫回。

本次改寫：限定同程序、同一 store instance 內這三步；不涵蓋外面的通知建立與入列，不擴稱跨程序或持久化交易。

理由：設計紀錄描述先前查核狀態，不能無條件套到 r2。程式註解也可能陳舊，必須核對方法實作。

## 「本輪未跑 .NET」的時間範圍

sources/design-review.md 第 7 點是當時設計查核的執行界線。Day17 已有新請求與工具資料，不能把這句當成所有後續都未執行。既有 Claude 回答已明確區分此點；本篇保留其原回答，不宣稱新 Wiki 已被模型讀取。

## 新 Wiki 的首次模型查核：同步分支

updated 與 unknown-version 回答指出 notify_sent 不只由 worker 寫入。作者對照 Program.cs:85-86、222 與257-260，接受此修訂，明列 sync_notify 分支。未整批接受模型提出的所有補充；來源副本不動。修訂後另跑 accepted 新 session。原模型回答與改前 Wiki 存在 runs/wiki-20261001-202117/。

## 將知識交給下一張工單

新增 applicability.md，列出結論、使用條件、不能推出的事、重新核對時機與下一步。兩次新 session 的合成工單查核保留在 runs/next-task-20261001-203725。兩輪都能識別同步路徑；before 額外建議補送沿用 ID，無人工補送契約支持，未接受。after 明列重複取消不是補送、要求方法與去重授權。每情境一次，不宣稱穩定改善。
