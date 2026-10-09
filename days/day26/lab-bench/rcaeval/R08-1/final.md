## 結論

**最可能根因是 `ts-route-service`**。它在 20:52–20:53 發生 rollout 或重啟,期間完全無法服務。呼叫它的 travel 系列服務因此回 5xx。不確定之處見文末。

### 證據

1. **ts-route-service 換了 pod 並重啟**
   - 事發前 log 只來自 pod `…6f78466fb7-7vhsk`(20:37:02 起)。
   - 20:52 起出現另兩個 pod:`…65944bc88b-gr5pm`(新 ReplicaSet hash)和 `…6f78466fb7-knws9`。
   - 20:53:17–20:53:28 出現 `main] route.RouteApplication : Started RouteApplicatio…`,同一分鐘有 112 行啟動 log。其他服務在該窗口都沒有啟動 log。

2. **ts-route-service 的請求量掉到 0**
   - `istio-request-total` 在 20:53:10–20:53:49 為 0 或 nan,共 40 筆。平常約 6–13 req/s。
   - `istio-latency-50` 同時為 nan,表示當時沒有回應。

3. **重啟時資源尖峰**
   - CPU 累計值在取樣點 t≈1000 由約 2–4 跳到 48.9。
   - memory 由約 250MB 升到 473–495MB,之後回到約 246MB。這符合重啟時 JVM 啟動的特徵。

4. **下游錯誤時間緊接在後**
   - `ts-travel2-service` 的 `istio-error-total` 在 20:52:48 起升到 0.4。
   - `ts-travel-service` 與 `ts-admin-travel-service` 在 20:52:53 起升到 0.333。
   - 這些服務的 ERROR log 只出現在 20:52–20:53:
     - ts-travel 48 筆
     - ts-travel2 36 筆
     - ts-admin-travel 28 筆
     - ts-food 8 筆
   - 典型 log:`HttpServerErrorException: 503 Service Unavailable`(travel、travel2),admin-travel 與 food 則是 500。

5. **trace 沒看到其他異常**
   - `statusCode` 欄全為空,無法用 trace 判斷錯誤。
   - 除了 order-other-service,各服務事發前後平均 duration 都沒有變慢。order-other 平均上升 1.25 倍,是因為少數 `refresh` span 約 25 萬 µs 拉高平均。各 endpoint 逐分鐘看沒有惡化,我判斷與事件無關。

### Top 3

1. **ts-route-service**:重啟、請求歸零,最早也最直接。
2. **ts-travel-service**(travel2 次之):最先出現 503 錯誤,是 route 的直接呼叫者,屬受害者而非源頭。
3. **ts-order-other-service**:唯一平均延遲上升的服務,但證據弱。

### 不確定之處

- **重啟原因不明**:是 rollout(新舊 ReplicaSet hash 並存)、OOM,還是人為操作,我沒有 k8s 事件可以確認。
- **時間差**:使用者回報的起點是 20:54,但錯誤在 20:52:48 就開始,比回報早約 1 分鐘。
- **記憶體指標有雜訊**:數個 mongo 容器的 `memory-failures-total` 事發後從 0 變成非 0,我在比較時算出極大的 z 值。但它在 40 多個容器的時間點分散,從 20:49 到 21:00 都有,跟 route 的重啟時間對不上。我視為背景雜訊,沒有納入。
- **兩個舊 pod 的 log 在 20:52 之後仍持續**:我沒有查清楚是逐步切換,還是兩組 pod 同時在服務。
- **ts-food-service**:只有 8 筆 500,其 `istio-error` 指標沒有超過 0.3 的點,與 route 的關聯較弱。

```json
{"root_cause_service": "ts-route-service", "top3": ["ts-route-service", "ts-travel-service", "ts-order-other-service"], "evidence": ["ts-route-service 20:53:28 出現 'Started RouteApplication' 啟動 log,且 20:52 起出現新 pod (…65944bc88b-gr5pm, …6f78466fb7-knws9)", "ts-route-service istio-request-total 在 20:53:10–20:53:49 為 0/nan(40 筆),平常約 6–13 req/s,latency-50 同時為 nan", "ts-route-service CPU 累計值由約 2–4 跳到 48.9,memory 由約 250MB 升到約 473–495MB 後回落", "ts-travel2 istio-error-total 20:52:48 起 0.4;ts-travel 與 ts-admin-travel 20:52:53 起 0.333", "ERROR log 僅出現在 20:52–20:53:ts-travel 48、ts-travel2 36、ts-admin-travel 28、ts-food 8,內容為 503/500 HttpServerErrorException"], "uncertain": ["重啟原因(rollout、OOM 或人為)無 k8s 事件可確認", "使用者回報 20:54 比錯誤起點 20:52:48 晚約 1 分鐘", "mongo 的 memory-failures-total 時間分散,視為雜訊,未驗證", "ts-food-service 僅 8 筆 500,與 route 的關聯較弱", "traces 的 statusCode 全空,無法用 trace 確認錯誤傳播路徑"]}
```