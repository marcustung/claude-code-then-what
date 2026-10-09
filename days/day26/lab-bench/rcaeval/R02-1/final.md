**根因服務:emailservice。** 它大約在 15:25 UTC 開始反覆崩潰重啟,比回報的 15:28 早約 3 分鐘。以下以 15:28:00 UTC(epoch 1732289280)當 T。

## 證據

1. **emailservice 啟動即崩潰(logs)**
   - 它反覆印出 `Traceback ... /email_server/email_server.py, line 199, in <module> start(dum...` 和 `Exception: non-dummy mode not implemented yet`。
   - 共 8 組,出現在 T-175、-168、-151、-116、-59、+39、+213、+521 秒,間隔不規則,看起來像 crash loop。
   - 第一次出現在 T-175 秒(約 15:25:05),早於使用者回報的時間。

2. **emailservice 的 trace 消失(traces)**
   - emailservice 在基準期有 152 個 span,平均耗時 162µs。
   - 它最後一個 span 在 T-188 秒,T 之後是 0 個 span。
   - 這個消失發生在第一次崩潰之前,所以我不確定是流量先停、還是服務先停。

3. **emailservice 的 metrics 也顯示服務掉了**

   | 指標 | 事發前 | 事發後 |
   |---|---|---|
   | memory-rss | 49.9MB | 9.2MB |
   | working-set | 54.0MB | 10.6MB |
   | sockets | 3.69 | 0.51 |
   | istio-request-total | 0.352 | 0.017 |
   | istio-latency p99 | 0.036 | 0.206 |

   在所有 metrics 裡,這幾項屬於變化最明顯的。記憶體大幅下降符合容器被重啟。

4. **下游 checkoutservice 受影響(logs、traces)**
   - 有 136 筆 `failed to send order confirmation to "...": rpc error: code = Unavailable desc = no healthy upstream`(部分是 `upstream ...`)。
   - 時間從 T-176 到 T+530 秒,和 emailservice 的崩潰時段重合。
   - checkoutservice 的 trace 錯誤數從事發前的 32 增加到事發後的 106。
   - 這些錯誤的 statusCode 多為 `14.0`(UNAVAILABLE),全部 trace 共 136 筆,數字和上面的 log 筆數一致。
   - checkoutservice 的平均耗時沒有惡化(6600µs 變 6148µs)。

5. **其他服務沒有明顯變化(traces)**
   - frontend 平均耗時是 6589µs,事發前後相同,錯誤數為 1 對 0。
   - currencyservice、productcatalogservice、paymentservice 的耗時前後幾乎一樣。

## 前三名

1. **emailservice**:崩潰最早,有直接的 traceback,metrics 也跟著變。
2. **checkoutservice**:它是 emailservice 的呼叫端,錯誤集中在發送訂單確認信。它應該是被牽連的症狀,不是起因。
3. **frontend**:它是使用者看到變慢或失敗的入口。但它自己的數據沒有變化,所以排第三只是因為使用者症狀出現在這裡,證據很弱。

## 不確定的地方

- `non-dummy mode not implemented yet` 是 emailservice 啟動時的設定問題。log 沒有顯示是誰改了設定、為什麼剛好那時重啟,我只能確定症狀,不能確定觸發原因。
- 我看到的崩潰、「使用者操作變慢或失敗」和 frontend 的數據不太吻合。frontend 的耗時沒變,可能是事發前後的取樣方式不同,也可能影響只出現在結帳流程。
- 事發後 emailservice 沒有 trace,但 istio-request-total 仍有 0.017,可能是少量健康檢查或重試。
- 我沒有逐一檢查所有欄位,只用「事發後平均值減事發前平均值,再除以事發前標準差」挑出變化最大的指標。
- 節點 `ip-192-168-6-79` 的 disk-reads 變化最大(5.4σ),但數值很小(0.001 變 0.027)。我不認為它和這次事件有關,也沒有深入查。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "frontend"], "evidence": ["emailservice logs: 8 組 Traceback + 'Exception: non-dummy mode not implemented yet',從 T-175s 開始,T 為 15:28:00 UTC", "emailservice traces: 基準期 152 個 span,最後一個在 T-188s,T 之後 0 個", "emailservice metrics: memory-rss 49.9MB→9.2MB, sockets 3.69→0.51, istio-request-total 0.352→0.017, istio-latency-99 0.036→0.206", "checkoutservice: 136 筆 'failed to send order confirmation ... Unavailable ... no healthy upstream'(T-176s 到 T+530s),trace 錯誤數 32→106(statusCode 14.0 共 136 筆)", "frontend 平均耗時 6589µs 前後不變,錯誤 1→0"], "uncertain": ["崩潰的觸發原因(為何出現 non-dummy mode 錯誤、為何重啟)在 log 中看不出來", "emailservice trace 消失(T-188s)略早於第一次崩潰 log(T-175s),先後順序不確定", "frontend 沒有明顯劣化,與使用者回報的『操作變慢』不完全吻合", "只用事發前後平均值差/標準差篩選 metrics,未逐一檢視所有欄位", "事發後 emailservice 仍有 istio-request-total 0.017,來源不明"]}
```