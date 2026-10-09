## 結論

**最可能的根因是 `ts-auth-service`**。信心中等:時間點吻合,但我沒找到 auth 的明確錯誤訊息。

## 證據

**1. 17:55 前後 auth-service 的 pod 換了一輪。**
- 舊 pod `ts-auth-service-75dfb9459b-5dwch` 的最後一筆 log 在 1733594097(約 17:54:57)。
- 新 ReplicaSet 的 pod `89d77f76b-h6fpt` 從 1733594082(17:54:42)開始出現。
- 舊 ReplicaSet 的 `75dfb9459b-t6v6s` 在 17:55:00 又啟動過一次,只活到約 17:55:52,共 35 筆 log。
- 這段時間出現 otel javaagent 與 Spring 的啟動 log(`[main] ... Creating filter chain`、`Mapped "{[/heapdump ...`)。

**2. 事發點之後,業務流量幾乎消失,只剩登入。**

| 時間 | 該分鐘 trace 總數 | 其中 auth-service |
|---|---|---|
| 17:54 | 6070 | 115 |
| 17:55 | 4354 | 5 |
| 17:56 | 216 | 191 |
| 17:57 到 18:09 | 每分鐘約 180–208 | 幾乎全部 |

- 17:56 起,非 auth 服務的 trace 在 13 分鐘內只剩 6 筆(station、food、route、travel 等)。
- 非 auth 服務最後一筆 span 的 startTimeMillis 是 1733594159958(約 17:55:59)。
- 事發前每分鐘有數千筆 span,station-service 就有 15821 筆。

**3. auth-service 本身的延遲沒有變差。**
- `POST /api/v1/users/login` 平均約 215ms(366 筆)變成約 222ms(652 筆)。
- 整體平均從 48ms 升到 113ms,是因為事發後只剩登入這種長 span,屬於組成改變。不要把它當成 auth 變慢。
- `find ts-auth-mongo.user` 平均約 3.5ms,前後相同,所以 auth-mongo 看起來正常。

**4. 事發前的 ERROR 是無關雜訊。**
- `ts-order-other-service` 在 17:55:10 有 `IllegalArgumentException: Invalid UUID string:`。
- 事發後 ERROR/WARN/Exception 類 log 為 0 筆。
- 事發後 `ts-ui-dashboard` 每分鐘約 45–52 筆 log,它仍在收請求。

**5. metrics 沒有明確的資源異常。**
- 我用 1 秒取樣的指標比較前後差異,最大的是 `ts_container-network-receive-bytes-total`,從 143 升到 657。
- 各服務 `istio-bytes-50` 從約 1.75 降到約 1.0,與流量下降一致。
- 有幾個欄位(例如 `node-disk-read-bytes-total`)基準值為 0,比較數字沒有意義,我不拿來當證據。

## 推論
我的推論是 auth-service 在 17:54:42–17:55:52 被重新部署或重啟,而 token 換發中斷。事發後登入仍持續成功,但其他業務 API 的呼叫沒有再出現。

## 不確定之處
- 我沒看到 auth-service 的錯誤 log,無法確定是重新部署、OOM 還是 crash。
- 「token 失效導致下游無流量」只是推論。也可能是 ui-dashboard 或 load generator 在 17:56 後只會重試登入。
- 我沒有查 ui-dashboard 的 log 內容。

**前三名候選:**
1. `ts-auth-service`:pod 輪替時間與流量崩塌時間吻合。
2. `ts-ui-dashboard`:閘道,事發後仍有流量,但我沒查它的內容。
3. `ts-auth-mongo`:17:55 該分鐘有 8 筆 log,是平時的數倍,但查詢延遲正常,可能只是重啟的附帶現象。

```json
{"root_cause_service": "ts-auth-service", "top3": ["ts-auth-service", "ts-ui-dashboard", "ts-auth-mongo"], "evidence": ["auth-service pod 輪替:舊 pod 5dwch 最後 log 約 17:54:57,新 RS pod h6fpt 自 17:54:42 出現,舊 RS pod t6v6s 17:55:00 又啟動、約 17:55:52 結束,並出現 otel/Spring 啟動 log", "每分鐘 trace 總數 17:54 為 6070、17:55 為 4354(其中 auth 僅 5),17:56 起降到約 180-216 且幾乎全是 auth 的登入;非 auth 服務最後 span 約 17:55:59,事發後僅剩 6 筆", "login 平均延遲約 215ms 變成約 222ms,auth-mongo find 約 3.5ms 前後不變,auth 本身未變慢", "事發後 ERROR/WARN/Exception 類 log 為 0 筆;事發前 order-other 有 Invalid UUID 例外,與事發無明顯關聯"], "uncertain": ["沒有 auth-service 的錯誤 log,無法確定是重新部署、OOM 還是 crash", "token 失效導致下游無流量只是推論,也可能是 ui-dashboard 或 load generator 的行為", "未檢查 ui-dashboard 的 log 內容", "metrics 沒有明確的資源異常指標可佐證"]}
```