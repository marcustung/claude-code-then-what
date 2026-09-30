# 可重跑入口：build → 啟 sink 與 api → readiness → 固定輸入 → 等終態或 timeout → 匯出 → 對帳 → 停止。
#   powershell -NoProfile -File tools/run.ps1 -scenario baseline
#   powershell -NoProfile -File tools/run.ps1 -scenario missing-notification
# 輸出 evidence/runs/<scenario>-<yyyyMMdd-HHmmss>/：logs.jsonl（服務）、receipts.jsonl（接收端）、requests.jsonl（客戶端）、metrics.txt、manifest.json、check.json
# 缺件、格式錯、timeout 都會讓 check.py 回非零 exit code；不會被當成功。
param([string]$scenario = 'baseline', [int]$apiPort = 5080, [int]$sinkPort = 5081, [switch]$noBuild)
$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false)
$root = Split-Path $PSScriptRoot -Parent
$scen = Get-Content (Join-Path $root "scenarios/$scenario.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runId = "$scenario-$stamp"
$runDir = Join-Path $root "evidence/runs/$runId"; New-Item -ItemType Directory -Force $runDir | Out-Null
$version = (Get-Content (Join-Path $root 'VERSION') -Raw).Trim()
$faultsPath = if ($scen.faults) { Join-Path $root $scen.faults } else { $null }

if (-not $noBuild) {
  foreach ($p in 'src/Domain/Domain.csproj','src/Api/Api.csproj','src/FakeSink/FakeSink.csproj') {
    $o = & dotnet build (Join-Path $root $p) -nologo -v q 2>&1; if ($LASTEXITCODE -ne 0) { $o | Out-String | Write-Host; throw "build failed: $p" }
  }
}
function Start-Svc($proj, $envs) {
  $psi = [Diagnostics.ProcessStartInfo]::new('dotnet', "run --no-build --project `"$(Join-Path $root $proj)`"")
  $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.WorkingDirectory = $root
  foreach ($k in $envs.Keys) { $psi.Environment[$k] = $envs[$k] }
  $p = [Diagnostics.Process]::Start($psi); $p.BeginOutputReadLine(); $p.BeginErrorReadLine(); return $p
}
function Wait-Ready($url, $seconds) {
  $deadline = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $deadline) { try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { return $true } } catch { } Start-Sleep -Milliseconds 200 }
  return $false
}
$sinkEnv = @{ OC_RUN_DIR = $runDir; ASPNETCORE_URLS = "http://127.0.0.1:$sinkPort" }
$apiEnv  = @{ OC_RUN_DIR = $runDir; ASPNETCORE_URLS = "http://127.0.0.1:$apiPort"; OC_SINK_URL = "http://127.0.0.1:$sinkPort/notify" }
if ($faultsPath) { $apiEnv.OC_FAULTS = $faultsPath }
$started = Get-Date
$sink = Start-Svc 'src/FakeSink/FakeSink.csproj' $sinkEnv
$api  = Start-Svc 'src/Api/Api.csproj' $apiEnv
$status = 'started'
try {
  if (-not (Wait-Ready "http://127.0.0.1:$sinkPort/health" 30)) { throw 'sink not ready' }
  if (-not (Wait-Ready "http://127.0.0.1:$apiPort/ready" 30)) { throw 'api not ready' }
  $reqLog = Join-Path $runDir 'requests.jsonl'
  # 固定輸入：建單
  foreach ($o in $scen.orders) {
    $body = @{ id = $o.id; shipped = [bool]$o.shipped; paid = [bool]$o.paid } | ConvertTo-Json -Compress
    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$apiPort/orders" -Body $body -ContentType 'application/json' -Headers @{ 'X-Run-Id' = $runId } | Out-Null
  }
  # 固定輸入：操作（每筆自帶 request_id，客戶端也記一行）
  $i = 0
  foreach ($op in $scen.operations) {
    $i++; $rid = ('{0}-r{1:d3}' -f $scenario, $i)
    $headers = @{ 'X-Request-Id' = $rid; 'X-Run-Id' = $runId }
    $actor = if ($op.PSObject.Properties['actor']) { $op.actor } else { 'tester' }
    if ($actor -ne '') { $headers['X-Actor'] = $actor }
    $code = 0; $resp = $null
    try { $r = Invoke-WebRequest -Method Post -Uri "http://127.0.0.1:$apiPort/orders/$($op.id)/cancel" -Headers $headers -UseBasicParsing -TimeoutSec 10; $code = [int]$r.StatusCode; $resp = $r.Content }
    catch { $code = [int]$_.Exception.Response.StatusCode; try { $resp = (New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd() } catch { $resp = '' } }
    $rec = @{ seq = $i; request_id = $rid; run_id = $runId; op = $op.op; order_id = $op.id; actor = $actor; http_status = $code; response = $resp; sent_at = (Get-Date).ToString('o') } | ConvertTo-Json -Compress
    Add-Content -Path $reqLog -Value $rec -Encoding UTF8
  }
  # 等終態：receipts 達期待且佇列排空；或 receipts 連續三次不變且佇列排空（故障情境）；或 timeout
  $deadline = (Get-Date).AddSeconds([int]$scen.wait.timeout_seconds)
  $stable = 0; $last = -1; $terminal = $false; $lastDepth = -1
  while ((Get-Date) -lt $deadline) {
    $rc = (Invoke-RestMethod -Uri "http://127.0.0.1:$sinkPort/receipts" -TimeoutSec 5).received
    $m = (Invoke-WebRequest -Uri "http://127.0.0.1:$apiPort/metrics" -UseBasicParsing -TimeoutSec 5).Content
    $depth = [int](($m -split "`n" | Where-Object { $_ -like 'oc_notify_queue_depth *' }) -replace 'oc_notify_queue_depth ', '')
    if ($rc -eq $last) { $stable++ } else { $stable = 0; $last = $rc }
    $lastDepth = $depth
    if ($depth -eq 0 -and $rc -ge [int]$scen.expected.notifications_received) { $terminal = $true; break }
    if ($depth -eq 0 -and $stable -ge 3) { $terminal = $true; break }
    Start-Sleep -Milliseconds 500
  }
  $status = if ($terminal) { 'terminal' } else { 'timeout' }
  Start-Sleep -Milliseconds 300
  (Invoke-WebRequest -Uri "http://127.0.0.1:$apiPort/metrics" -UseBasicParsing).Content | Set-Content (Join-Path $runDir 'metrics.txt') -Encoding UTF8
  # 最終狀態回讀（NC-04：狀態已改 ≠ API 接受）
  $states = @{}
  foreach ($o in $scen.orders) { try { $states[$o.id] = (Invoke-RestMethod -Uri "http://127.0.0.1:$apiPort/orders/$($o.id)").order } catch { $states[$o.id] = $null } }
  $states | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $runDir 'final-states.json') -Encoding UTF8
}
finally {
  foreach ($p in @($api, $sink)) { if ($p -and -not $p.HasExited) { & taskkill /PID $p.Id /T /F 2>$null | Out-Null; $p.WaitForExit(5000) | Out-Null } }   # dotnet run 有子程序，殺整棵樹
}
$manifest = @{
  run_id = $runId; scenario = $scenario; version = $version; status = $status; started = $started.ToString('o'); ended = (Get-Date).ToString('o')
  faults_file = $scen.faults; faults_sha256 = if ($faultsPath) { (Get-FileHash $faultsPath -Algorithm SHA256).Hash } else { $null }
  scenario_sha256 = (Get-FileHash (Join-Path $root "scenarios/$scenario.json") -Algorithm SHA256).Hash
  domain_sha256 = (Get-FileHash (Join-Path $root 'src/Domain/Cancellation.cs') -Algorithm SHA256).Hash
  api_sha256 = (Get-FileHash (Join-Path $root 'src/Api/Program.cs') -Algorithm SHA256).Hash
  expected = $scen.expected; wait = $scen.wait; api_port = $apiPort; sink_port = $sinkPort; last_queue_depth = $lastDepth
  human = @{ prepare_min = $null; operate_min = $null; review_min = $null; rework_min = $null; wait_min = $null; note = '人工欄位由作者填；null＝未記錄，不是零' }
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $runDir 'manifest.json') -Encoding UTF8
Write-Host "run: $runId  status=$status"
& python (Join-Path $root 'tools/check.py') $runDir
exit $LASTEXITCODE
