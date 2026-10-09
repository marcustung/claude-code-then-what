## 結論

最可能的根因是 **emailservice**。它的指標在 t≈+810s 開始異常,checkoutservice 隨後才跟著惡化。

這裡的 t 是指標檔 `metrics.csv` 開頭(1705742053,約 09:14:13 UTC)起算的秒數。+810s 約為 09:27:43。我用 09:29 (1705742940) 當事發前後的分界。

### 證據

**1. emailservice 資源與延遲在 +810s 起跳**
- `emailservice_istio-latency-95` 在 +720s 前一直是 0.005s,+810s 變成 0.241,+1260s 到 2.275。事發前平均 0.052,之後平均 0.66。
- RSS 記憶體約 40.6MB,在 +810s 突然變成 81.3MB,+1260s 為 121MB,+1350s 為 162MB。每次增加約 40MB。
- sockets 從 3 升到 6,後來到 13。
- `memory-failures-total` 平均從 24.9 變成 115.1。
- 事發前後的變化幅度,emailservice 的指標在所有服務中最顯著,排在 node 磁碟讀取計數之後(見下方不確定項)。

**2. checkoutservice 的惡化晚於 emailservice**
- `checkoutservice_istio-latency-95` 在 +720s 前穩定在約 0.24s。+810s 起為 0.485,+1260s 到 3.31。事發前平均 0.30,之後平均 1.02。
- checkoutservice 的 trace 平均耗時從 18,070µs 變成 35,538µs,p95 從 82,458 變成 120,351。
- checkoutservice 的 warning log 共 9 筆(事發前 1 筆),內容都是:`failed to send order confirmation to "someone@example.com": rpc error: code = Unavailable desc = no healthy upstream`。
- 這個錯誤訊息直接指向 emailservice 這個下游依賴。

**3. 其他服務沒有明顯變化**
- currencyservice、productcatalogservice、recommendationservice、paymentservice、frontend 的 trace 平均耗時事發前後差距在 10% 以內。
- 這些服務的 trace 錯誤數都是 0。

### 前三名

1. **emailservice**:最先異常,記憶體階梯式上升、延遲飆高,並有 `no healthy upstream` 錯誤。
2. **checkoutservice**:延遲與錯誤是症狀,從 emailservice 傳導而來。它同步呼叫 emailservice,所以被拖慢。
3. **frontend**:使用者看到的慢或失敗可能經由它呈現,但 trace 耗時只從 12,615µs 變成 13,388µs,幾乎沒變。這個排名是依傳導路徑推測。

### 不確定之處

- 異常最早出現在 +810s(約 09:27:43),比回報的 09:29 早約 1 分多鐘。我沒有進一步查明這段落差。
- emailservice 記憶體呈 40MB 的整數倍階梯上升,可能是記憶體洩漏或容器重啟。+1080s 曾掉回 40MB,這點支持重啟的可能,但我沒查重啟計數,所以無法確定。
- 影響範圍比較像是 checkout 流程,不是全站。frontend 的 trace 耗時幾乎沒變,而 checkoutservice 的 warning 只有 9 筆,所以我無法確認使用者看到的「有些操作變慢」是不是全部由此造成。
- node 磁碟讀取指標(`...0e4z_node-disk-read-bytes-total`)從 0 變成 317.9,z 分數最高。這個基準值是 0,所以分數很可能是人為放大。我判斷這與服務無關,但沒有進一步確認。
- emailservice 的 trace 數量從 751 變成 411。事發後資料窗口較短,所以這個變化不能直接解讀。我也沒有檢查它的 trace 錯誤碼細節。

```json
{"root_cause_service": "emailservice", "top3": ["emailservice", "checkoutservice", "frontend"], "evidence": ["emailservice_istio-latency-95 從 0.005s(+720s 前)升到 0.241(+810s),+1260s 達 2.275;事發前平均 0.052、之後平均 0.66", "emailservice RSS 約 40.6MB 在 +810s 變成 81.3MB,+1260s 為 121MB,+1350s 為 162MB;sockets 3→13;memory-failures-total 平均 24.9→115.1", "checkoutservice istio-latency-95 事發前平均 0.30、之後 1.02,晚於 emailservice 開始上升", "checkoutservice log: failed to send order confirmation to \"someone@example.com\": rpc error: code = Unavailable desc = no healthy upstream(共 9 筆事發後)", "其他服務 trace 平均耗時事發前後變化在 10% 以內,錯誤數為 0"], "uncertain": ["異常起點約 09:27:43,早於回報的 09:29,未查明落差", "記憶體 40MB 階梯式上升,可能是洩漏或重啟,未查重啟計數", "只影響 checkout 流程,無法確認是否解釋全部使用者症狀", "node 磁碟讀取指標 0→317.9 疑為基準為 0 造成的放大,未進一步確認", "emailservice 事發前後 trace 數量 751→411,窗口長度不同,未細查錯誤碼"]}
```