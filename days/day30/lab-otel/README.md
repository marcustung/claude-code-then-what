# Day 30 OTel 實驗：Claude Code 自己的遙測看得到什麼

文章：Day 30（回到 Day 1 總經理的問題）

用 Day 28 的通知檢查跑兩組（A1 重疊、C1 沒權限），打開 Claude Code 的 OpenTelemetry 遙測，送到本機一支小接收程式，看遙測比後台看板多看到什麼、仍然看不到什麼。結果見 `criteria.md`。

## 這裡有什麼

| 檔案 | 用途 |
|---|---|
| `criteria.md` | 跑前寫定的五個問題與預期；跑後追加的結果與觀察 |
| `otlp_receiver.py` | 約 30 行的本機 OTLP/HTTP-JSON 接收程式，把 metrics、logs 原樣存成 JSONL |
| `run.py`、`service.py`、`tool_*.py.tmpl` | 複製自 Day 28；唯一改動是每輪加上 `OTEL_RESOURCE_ATTRIBUTES=lab.group=…,lab.run=…` |
| `runs/20261012T030354Z/` | 本次實跑：各組服務端紀錄與摘要；`otel/metrics.jsonl`、`otel/logs.jsonl` 是收到的遙測（身分欄位與外掛名稱已改成 `<REDACTED>`） |

## 怎麼跑

需要 Python 3 與 Claude Code CLI。約 US$0.06。

```powershell
python otlp_receiver.py otel 4318          # 另開一個視窗，讓它一直跑
$env:CLAUDE_CODE_ENABLE_TELEMETRY="1"; $env:OTEL_METRICS_EXPORTER="otlp"; $env:OTEL_LOGS_EXPORTER="otlp"
$env:OTEL_EXPORTER_OTLP_PROTOCOL="http/json"; $env:OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:4318"
$env:OTEL_METRIC_EXPORT_INTERVAL="5000"; $env:OTEL_LOGS_EXPORT_INTERVAL="2000"
python run.py A1 C1
```

看 `otel/logs.jsonl` 裡的 `tool_decision`（C1 是 reject）、`tool_result`（A1 兩輪都是 success），再對照 `runs/*/A1/items.json` 的 4 張單。

## 界線

各組一次，示範遙測內容。提示與回覆預設遮掉（沒開 `OTEL_LOG_USER_PROMPTS`）；但每筆事件都帶使用者 email、帳號與組織 ID，收進共用平台前要先決定存取與保存規則。
