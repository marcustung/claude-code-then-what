我已更新同一個 Dashboard（UID `day25-work-view-v7`，資料夾 `day25`），只改了「AI 判斷，待確認」區塊的表格。更新後我用 gcx 查了一次 `work_ai_card`，回傳 2 筆（`sep-missing`、`sep-slow`）。我也確認伺服器上存的查詢已經是新的 `work_ai_card`。

**改了什麼**
- **查詢：** 從 `work_ai_hint` 改成 `work_ai_card`，取 `question`、`answer`、`verified`、`first_step`、`generated_at`。文字照資料顯示，沒有改寫。
- **欄位：** 依序是「問了什麼、判斷、用查詢驗證到什麼、先查哪裡、產生時間」。
- **舊欄位：** 原本的「影響」和「AI 自評把握」兩欄拿掉了。「影響」是舊查詢用 `work_status` 接出來的，`work_ai_card` 沒有 `impact` 標籤，所以連同那段接法和排序一起移除。「AI 自評把握」對應的 `confidence` 標籤也不在新資料裡。
- **欄寬：** 「問了什麼」和「產生時間」留了固定寬度，原本的「影響」和「AI 自評把握」兩個寬度設定也移除了。

其他面板、版面、用詞、面板標題、顏色和折行設定都沒動。

**更新方式**
- 第一次更新被拒絕，因為伺服器預期 v2 API。我改用 `--api-version dashboard.grafana.app/v1beta1` 才成功。
- `dashboard.json` 的 metadata 多了一個 `resourceVersion`，更新需要它。
- 我沒有另外做畫面截圖。

最後的定義存在 `dashboard.json`。