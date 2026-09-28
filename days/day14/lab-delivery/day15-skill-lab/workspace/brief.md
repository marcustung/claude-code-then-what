# Independent planning inputs
Teaching order cancellation API. Read both C# files to discover endpoints and architecture.
Requirements: shipped orders cannot be cancelled; paid unshipped orders request refund once (flag only, no actual payment); repeated cancellation must not add notifications; each transition should have one receiver receipt.
Environment: Windows loopback, .NET9, k6 1.3.0 CLI available to external runner; no production traffic, no company SLA. Target is the existing unchanged packaged service. No service code edits permitted in this experiment.
Predeclared teaching criteria: first cancellation p95<250ms, HTTP failure rate 0 for expected-success workloads, all behavior checks pass, no dropped iterations. These are NOT production promises. Suggested additional bounds must be labeled hypotheses for confirmation.
Budget: recommend ONE highest-value additional local experiment, <=60 seconds load, <=10 new orders/sec, <=50 VUs, <=20sec post-load drain. Need expected observations, evidence and stop rules before execution. Longer soak is outside this run.
No MCP available. Tools limited to Read/Grep/Glob/Skill. Do not claim MCP/version/doc queries executed. Planner research step not available; state limitation.
