## 結論

最可能的根因是 **ts-auth-service**。它的 Pod 在 17:54:57 被換掉，之後登入變慢，其他服務的流量也大量消失。

## 證據

1. **ts-auth-service 先出事（17:54:57 起）**
   - 舊 Pod `ts-auth-service-75dfb9459b-5dwch` 在 17:54:56–57 開始關閉。log 有 `Closing ...ApplicationContext`、`Stopping beans in phase 0`、`Closed connection ... to ts-auth-mongo:27017`。
   - 17:55:22 起出現新的 ReplicaSet Pod `ts-auth-service-89d77f76b-h6fpt`，17:55:52 `Started AuthApplication in 49.797 seconds`。
   - 17:55:39 同時有另一個 Pod `75dfb9459b-t6v6s` 在啟動。也就是 auth-service 在這段時間被重建，疑似 rollout 或設定變更。
   - 17:54–17:55 的 WARN/ERROR 關鍵字 log 只有 16 筆，都是關閉流程的正常訊息，沒有看到明確的錯誤。

2. **登入延遲變成約 2.4 倍**
   - auth-service span 平均耗時：事發前 48,132 µs，事發後 112,664 µs。
   - 逐分鐘看，17:39–17:54 約 41–53 ms，17:56 之後約 98–126 ms，且持續沒有恢復。
   - 17:55 那一分鐘只有 5 個 span，平均 580 ms，這是重啟空窗。

3. **其他服務的 span 量崩塌**
   - 全系統 traces 每分鐘從約 3,000–8,000 筆，在 17:55 後掉到 100–216 筆。
   - 17:57 之後仍有 span 的只剩 auth-service 的 `POST /api/v1/users/login`、`UserController.getToken`、`UserRepository.findByUsername`、`find ts-auth-mongo.user`，各 605 筆。
   - 我的解讀是登入受阻，所以後續請求沒有進來。
   - Istio 指標也一致：`ts-travel-service_istio-bytes-99` 從 2.48 掉到 0.18，ticketinfo、seat、train 等也一樣。

4. **auth-service 資源在重啟後異常**
   - CPU usage 累計值：正常時約 5 左右，重啟期間變成 52、78、63，之後回到 10.8 和 8.3。這代表 JVM 啟動期間 CPU 吃很重。
   - 記憶體 working set：約 20 MB 先升到 41–54 MB，之後又回到 20.8 MB。

5. **ts-auth-mongo 看起來正常**
   - CPU 約 0.32–0.41，記憶體約 64.6–65.1 MB，事發前後沒有明顯變化。
   - 它在 17:54:57 的連線結束是 auth-service 主動關閉連線造成的。

## 前 3 名候選

1. **ts-auth-service**：時間最早，有重建的直接證據，登入延遲也明顯上升。
2. **ts-auth-mongo**：登入的下游依賴，所以列為候選。但它的指標沒有異常，可能性低。
3. **ts-ui-dashboard**：入口服務，流量崩塌會在這裡看到。我沒有查它的失敗請求，所以只是候選。

## 不確定之處

- 我沒有直接看到 auth-service 被重建的原因，例如部署變更、OOM 或 liveness 失敗，需要 Kubernetes 事件才能確認。
- 重啟後延遲仍維持約 110 ms。我不能確定這是新版本本身變慢，還是下游或負載造成的。
- 流量崩塌也可能只是壓測腳本在登入失敗時停止發請求，所以我不能排除它是測試端的因素。
- 在 metrics 的統計裡，變化最大的是 `ts-news-service` 的記憶體失敗計數、node `ip-192-168-55-200` 的磁碟讀取，以及 `ts-avatar-service` 的 CPU。這些的事發前基準值都是 0，我沒有進一步查它們與事件的關係。
- 時間分界我用 17:56:00 UTC（epoch 1733594160）。metrics 的 NaN/inf 值我按 0 處理。

```json
{"root_cause_service": "ts-auth-service", "top3": ["ts-auth-service", "ts-auth-mongo", "ts-ui-dashboard"], "evidence": ["17:54:56-57 舊 Pod ts-auth-service-75dfb9459b-5dwch 關閉(Closing ApplicationContext, Closed connection to ts-auth-mongo)", "17:55:22 新 ReplicaSet Pod 89d77f76b-h6fpt 啟動，17:55:52 'Started AuthApplication in 49.797 seconds'", "auth-service span 平均耗時 48,132µs -> 112,664µs (約2.3x)，17:56 後穩定在約100-126ms", "全系統 traces 每分鐘約3000-8000筆 -> 17:56後100-216筆，17:57後只剩 auth login 相關 span (各605筆)", "ts-travel-service_istio-bytes-99 由 2.48 降到 0.18，其他服務同樣下降", "auth-service CPU usage 累計值重啟期間 52-78 (正常約5)，ts-auth-mongo CPU/記憶體無明顯變化"], "uncertain": ["重建原因(部署變更/OOM/liveness)缺少 k8s 事件", "重啟後延遲持續偏高的原因未確認", "流量崩塌可能是壓測端在登入失敗後停止發請求", "未檢查 ts-ui-dashboard 的失敗請求", "metrics 中基準為0的指標(news-service memory failures、node 磁碟讀取、avatar-service CPU)與事件的關係未查"]}
```