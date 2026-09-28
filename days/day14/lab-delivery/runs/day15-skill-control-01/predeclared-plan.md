# Supplementary plan (written before execution)
Official planner loaded successfully, but recommended sent logs alone do not establish receiver delivery.
Adopt its preseeded first-cancellation workload. Author selects two downstream conditions to test its queue risk.
Same existing candidate-checked package, unchanged hashes. Fresh service each run; no rebuild.
210 paid/unshipped orders seeded before load. 10 first cancellations/sec for 20 sec, <=50 VUs.
Control receiver responds immediately; slow receiver waits 300ms before recording receipt/responding 200. This is artificial latency, not production measurement.
API acceptance: first-cancel p95<250ms, HTTP error 0, checks100%, dropped0.
Delivery acceptance: after load, <=20sec drain; each transitioned notification ID must have exactly one receiver receipt and corresponding sent log. 20sec is a teaching observation deadline, not SLA. Missing receipts at cutoff mean incomplete by cutoff, not proven loss.
Stop service at cutoff; report actual counts. Compare control vs slow under identical workload. Not comparable to old four-request mixed workflow p95 as a performance improvement.
No MCP. New script and orchestration written locally after Claude's planning; Claude did not execute k6.
New experiment saves local JSON and metrics samples; not added to existing Grafana screenshot.
