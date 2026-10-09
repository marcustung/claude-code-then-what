# 根因分析：emailservice

## 結論
最可能的根因是 **emailservice**。它的 gRPC 伺服器程式有錯誤並崩潰重啟，checkoutservice 因此寄不出訂單確認信。

## 證據
1. **emailservice 的 log 最早出現錯誤。** 錯誤訊息是 `AttributeError: '_Server' object has no attribute 'Check'`。第一筆在 14:22:12（timestamp 1732371732），比回報時間 14:24 早約 2 分鐘。之後每隔幾十秒重複出現，共 8 筆錯誤，另有 `Traceback ... email_server.py line 199, start(dummy_mode = True)` 和 `starting the email service in dummy mode`。
   - 這像是健康檢查 `Check` 沒有實作，服務啟動失敗後反覆重啟。
   - 14:28:48 和 14:33:48 又看到重啟，所以 14:27 起的 metrics 空窗與反覆重啟相符。
2. **emailservice 的 metrics 在 1732372018（約 14:26:58）消失。** 在 metrics 前後對比中，它的異常程度最高。
   - `container-sockets` 從 3 掉到 0。
   - `memory-rss` 從約 45.3MB 掉到約 4.5MB，之後再變成空值。
   - `cpu-usage`、網路收發封包事發後全為 0。
   - `istio-request-total` 從 0.329 掉到 0.002。
   - 事發前 `memory-rss` 平均約 41MB，事發後約 13.8MB，約 51 個標準差。
3. **traces 裡 emailservice 的 span 完全消失。** 14:24 之前有 121 筆（平均 196µs），14:24 之後是 0 筆。
4. **下游 checkoutservice 的錯誤是症狀。** logs 有 126 筆失敗訊息，例如 `failed to send order confirmation to "gmcdonald@example.net": rpc error: code = Unavailable desc = no healthy upstream`。
   - 另一種變體是 `upstream connect error or disconnect/reset before headers`。
   - 第一筆在 14:22:21，晚於 emailservice 的第一筆錯誤。
   - traces 裡 checkoutservice 的錯誤 span（statusCode 14.0）共 126 筆，這個數字與 log 的 126 筆一致。
   - 14:24 之後的 108 筆錯誤中，沒有 frontend 或其他服務出錯。

## Top 3 候選
1. **emailservice**：最先出錯，且指標和 trace 都消失。
2. **checkoutservice**：直接呼叫 emailservice 並產生所有錯誤，但是下游受害者，起點在 emailservice 之後。
3. **paymentservice**：證據很弱。
   - `network-receive-bytes` 從 262 升到 558，約 6 個標準差。
   - `memory-max-usage` 約 9.5 個標準差。
   - 沒有任何錯誤 log 或 trace 異常，可能只是訂單流程的連帶變化。

## 不確定之處
- 我沒有找到容器重啟的明確紀錄（例如 OOM 或 kill），也不知道 `Check` 錯誤是部署版本問題還是 dummy mode 設定問題。
- metrics 空窗（14:26:58）晚於 log 錯誤（14:22:12）約 5 分鐘，我無法確定中間這段是反覆重啟還是部分可用。
- 使用者回報的「變慢」，我在 frontend 沒看到延遲上升（平均 5703µs 對 5427µs），所以慢的感受主要來自結帳失敗或等待逾時，這一點沒有直接證據。
- 我用 14:24 當事發分界，以前後平均和標準差排序指標。這種比較對計數器類指標不嚴謹，只能當線索。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "paymentservice"], "evidence": ["emailservice log 自 14:22:12 起重複出現 AttributeError: '_Server' object has no attribute 'Check'，共 8 筆，並有 Traceback 與重啟訊息", "emailservice sockets 3→0、memory-rss 45.3MB→4.5MB（1732372018），cpu 與網路事發後為 0", "emailservice 在 traces 事發前 121 筆 span、事發後 0 筆", "checkoutservice 有 126 筆 'failed to send order confirmation ... Unavailable: no healthy upstream'，與 traces statusCode 14.0 的 126 筆一致，且第一筆（14:22:21）晚於 emailservice 第一筆錯誤"], "uncertain": ["沒有容器重啟或 OOM 的明確紀錄，錯誤成因（版本、dummy mode 或 Check 未實作）未確認", "log 錯誤（14:22:12）與 metrics 消失（14:26:58）相差約 5 分鐘，中間狀態不明", "frontend 延遲沒有明顯上升，使用者感受到的『變慢』沒有直接證據", "paymentservice 的流量與記憶體變化可能只是連帶效應，無錯誤佐證"]}
```