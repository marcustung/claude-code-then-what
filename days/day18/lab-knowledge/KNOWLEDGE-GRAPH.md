# Day 18｜LLM Wiki 關係圖實作附件（Claude Code 重跑）

## 這次實際做了什麼

用 **Claude Code** 的 `understand-anything` 外掛（article-analyzer agent）分析 Day 18 教學 Wiki，抽出知識圖的節點與關係。全程在 Claude Code 內完成，沒有使用其他廠商的工具或環境，也沒有讓它讀取公司資料。

- 輸入：`examples/day18-knowledge-lab/` 的 `wiki/`（INDEX、通知、Log 查詢、修訂、使用條件）與 `sources/`（Program.cs、Cancellation.cs、design-review.md）。
- 性質：這是 LLM 的語意抽取，不是確定性 parser 的計數；換次執行節點／關係數可能略有不同。本次抽出 15 節點、20 關係，正文圖取其主幹。

## 節點（15）

| # | 名稱 | 類型 |
|---|---|---|
| N1 | INDEX 知識入口 | wiki 頁 |
| N2 | 通知與取消頁 | wiki 頁 |
| N3 | Log 查詢頁 | wiki 頁 |
| N4 | 修訂紀錄頁 | wiki 頁 |
| N5 | 使用條件頁 | wiki 頁 |
| N6 | Program.cs | 來源程式 |
| N7 | Cancellation.cs | 來源程式 |
| N8 | design-review.md | 來源設計紀錄 |
| N9 | OrderStore.TryCancel（_g lock） | 程式元件 |
| N10 | Channel → NotificationWorker | 程式元件 |
| N11 | sync_notify / SendOnce 分支 | 程式元件（故障注入） |
| N12 | notify_sent 事件 | Log 事件 |
| N13 | 「送達未知 ≠ 未送達」 | 約束主張 |
| N14 | 接收端證據（同 notification_id） | 證據需求 |
| N15 | 人工補送授權 | 缺件／未取得決策 |

## 關係（20）

1. N1 分類到 N2
2. N1 分類到 N3
3. N1 分類到 N4
4. N1 分類到 N5
5. N1 環境與版本委派給 task.json（屬性，未建節點）
6. N2 來源指向 N6（定位 TryCancel）
7. N2 描述 N9
8. N9 同 lock 內呼叫 N7
9. N2 描述正常路徑 N10
10. N10 寫入 N12
11. N11 在請求路徑寫入 N12（帶 sync=true）
12. N6 定義 N11
13. N12 只證明發送端成功，不證明 N14
14. N13 約束 N3（零筆只能留 unknown）
15. N13 約束 N5
16. N5 排除推論 N15（無補送契約不得建立授權）
17. N4 修訂來源 N8 第 4 點（r2 已在同 lock 內，限定同程序）
18. N4 限定時間範圍 N8 第 7 點（「本輪未跑 .NET」不外推）
19. N4 記錄接受的修訂 N11（明列同步分支）
20. N7 重複取消 N5（重複取消不是補送入口）

## 作者歸屬邊檢查

檢查結果：**輸出中沒有任何 `authored_by` / `written_by` 指向 Claude 的邊**，也沒有「Claude → wiki 頁」的建立邊。

容易誘發這類錯邊的兩個來源，都刻意不轉成作者邊：

- `changes.md` 把模型回答與 wiki 修訂寫在一起，直覺會抽成 `Claude —authored→ 通知頁`。正確讀法是該段明寫「作者對照 `Program.cs:85-88`、222、257-260，接受此修訂」「未整批接受模型提出的所有補充」，所以 Claude 的角色是 `Claude —指出差異→ notify_sent 寫入點不只 worker`，再由 `作者 —核對來源並接受修訂→ 修訂紀錄頁`。
- `notification.md` 引用 `sources/claude-answer.md`，那是被引來源，邊應為 `通知頁 —引用→ claude-answer.md`，不是作者邊。

**結論：保留「作者：撰寫／核對」與「Claude：指出差異／提修訂建議」兩種角色邊，不合併成同一條 `authored_by`。** 混用會把「誰為內容正確負責」錯置，而這份 Wiki 能被信任的前提，正是維護責任留在人身上。

## 界線

- 這是一次 LLM 語意抽取的結果，不是確定性掃描；數字與邊會隨執行變動，不代表唯一正解。
- 關係圖幫維護者找到該回看的頁面；原文與程式才是核對判斷的依據。
- 只用 Day 18 教學 Wiki，未對正式服務查詢或補送，未改既有實跑。
