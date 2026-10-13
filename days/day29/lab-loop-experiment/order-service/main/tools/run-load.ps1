# 壓力情境入口：build → 啟 sink／api（可帶 env 與故障檔）→ readiness → tools/load.py 併發取消 → 每 500 ms 取樣 /metrics → 結束或程序崩潰 → 匯出 → 對帳 → 停止。
#   powershell -NoProfile -File tools/run-load.ps1 -scenario oom-retained-payloads
# 與 run.ps1 差別：捕捉 api 的 stdout／stderr（崩潰訊息）、metrics 時間線、程序退出碼；服務崩潰時 status=crashed，check 一律 FAIL。
param([string]$scenario = 'load-baseline', [int]$apiPort = 5080, [int]$sinkPort = 5081, [switch]$noBuild)
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
function Start-Svc($proj, $envs, $outFile, $errFile) {
  # 用 Start-Process 的檔案重導向接 stdout／stderr（不用事件處理器：程序退出瞬間的事件會在背景執行緒丟例外，殺掉整個 PowerShell）
  $saved = @{}
  foreach ($k in $envs.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $envs[$k]) }
  try {
    $p = Start-Process -FilePath 'dotnet' -ArgumentList @('run', '--no-build', '--project', (Join-Path $root $proj)) -WorkingDirectory $root -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
  } finally {
    foreach ($k in $envs.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) }
  }
  return @{ proc = $p }
}
function Wait-Ready($url, $seconds) {
  $deadline = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $deadline) { try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { return $true } } catch { } Start-Sleep -Milliseconds 200 }
  return $false
}
$sinkEnv = @{ OC_RUN_DIR = $runDir; ASPNETCORE_URLS = "http://127.0.0.1:$sinkPort" }
$apiEnv  = @{ OC_RUN_DIR = $runDir; ASPNETCORE_URLS = "http://127.0.0.1:$apiPort"; OC_SINK_URL = "http://127.0.0.1:$sinkPort/notify" }
if ($faultsPath) { $apiEnv.OC_FAULTS = $faultsPath }
if ($scen.PSObject.Properties['env'] -and $scen.env) { foreach ($pp in $scen.env.PSObject.Properties) { $apiEnv[$pp.Name] = [string]$pp.Value; if ($pp.Name -like 'OC_SINK_*') { $sinkEnv[$pp.Name] = [string]$pp.Value } } }
# 連接埠若被上一次沒收乾淨的服務占用，先停掉（否則 api 綁不上，負載會打到舊程序）
foreach ($port in @($apiPort, $sinkPort)) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "port $port busy (pid $($_.OwningProcess)) -> stop"; Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Milliseconds 300
$started = Get-Date
$sink = Start-Svc 'src/FakeSink/FakeSink.csproj' $sinkEnv (Join-Path $runDir 'sink-stdout.txt') (Join-Path $runDir 'sink-stderr.txt')
$api  = Start-Svc 'src/Api/Api.csproj' $apiEnv (Join-Path $runDir 'api-stdout.txt') (Join-Path $runDir 'api-stderr.txt')
$status = 'started'; $apiExit = $null; $loadSummary = $null
$timeline = Join-Path $runDir 'metrics-timeline.jsonl'
try {
  if (-not (Wait-Ready "http://127.0.0.1:$sinkPort/health" 30)) { throw 'sink not ready' }
  if (-not (Wait-Ready "http://127.0.0.1:$apiPort/ready" 30)) { throw 'api not ready' }
  # 負載在背景跑，前景每 500 ms 取樣 metrics；api 崩潰就停
  $L = $scen.load
  $loadArgs = "`"$(Join-Path $root 'tools/load.py')`" --api http://127.0.0.1:$apiPort --run-id $runId --out `"$runDir`" --orders $($L.orders) --concurrency $($L.concurrency) --payload-bytes $($L.payload_bytes) --repeat $($L.repeat) --seed $($L.seed)"
  $lpsi = [Diagnostics.ProcessStartInfo]::new('python', $loadArgs)
  $lpsi.UseShellExecute = $false; $lpsi.RedirectStandardOutput = $true; $lpsi.RedirectStandardError = $true; $lpsi.WorkingDirectory = $root
  $lp = [Diagnostics.Process]::Start($lpsi)
  $lo = $lp.StandardOutput.ReadToEndAsync(); $le = $lp.StandardError.ReadToEndAsync()
  $deadline = (Get-Date).AddSeconds([int]$scen.wait.timeout_seconds)
  while ((Get-Date) -lt $deadline) {
    if ($api.proc.HasExited) { $status = 'crashed'; $apiExit = $api.proc.ExitCode; break }
    try {
      $m = (Invoke-WebRequest -Uri "http://127.0.0.1:$apiPort/metrics" -UseBasicParsing -TimeoutSec 3).Content
      $g = @{}; foreach ($line in ($m -split "`n")) { if ($line -match '^(oc_gc_heap_bytes|oc_working_set_bytes|oc_notify_queue_depth|oc_request_latency_ms_count|oc_request_latency_ms_sum|oc_gc_collections_gen2) (\S+)$') { $g[$Matches[1]] = [double]$Matches[2] } }
      $g['ts'] = (Get-Date).ToString('o'); ($g | ConvertTo-Json -Compress) | Add-Content -Path $timeline -Encoding UTF8
    } catch { }
    if ($lp.HasExited) {
      # 負載結束：等佇列排空或穩定
      Start-Sleep -Milliseconds 800
      if (-not $api.proc.HasExited) { $status = 'terminal' } else { $status = 'crashed'; $apiExit = $api.proc.ExitCode }
      break
    }
    Start-Sleep -Milliseconds 500
  }
  if ($status -eq 'started') { $status = 'timeout' }
  if (-not $lp.HasExited) { $lp.Kill() }
  $lp.WaitForExit(5000) | Out-Null
  $loadSummary = $lo.Result; $le.Result | Set-Content (Join-Path $runDir 'load-stderr.txt') -Encoding UTF8
  if (-not $api.proc.HasExited) {
    try { (Invoke-WebRequest -Uri "http://127.0.0.1:$apiPort/metrics" -UseBasicParsing).Content | Set-Content (Join-Path $runDir 'metrics.txt') -Encoding UTF8 } catch { }
  }
  Start-Sleep -Milliseconds 500
}
finally {
  foreach ($h in @($api, $sink)) {
    try {
      if ($h -and -not $h.proc.HasExited) {
        # dotnet run 的子程序（Api.exe／FakeSink.exe）要一起停：先找子，再停父
        Get-CimInstance Win32_Process -Filter "ParentProcessId=$($h.proc.Id)" -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Stop-Process -Id $h.proc.Id -Force -ErrorAction SilentlyContinue
        $h.proc.WaitForExit(5000) | Out-Null
      }
    } catch { }
  }
  Start-Sleep -Milliseconds 300
}
$manifest = @{
  run_id = $runId; scenario = $scenario; mode = 'load'; version = $version; status = $status; api_exit_code = $apiExit; started = $started.ToString('o'); ended = (Get-Date).ToString('o')
  faults_file = $scen.faults; faults_sha256 = if ($faultsPath) { (Get-FileHash $faultsPath -Algorithm SHA256).Hash } else { $null }
  env = $scen.env; load = $scen.load; expected = $scen.expected; wait = $scen.wait
  scenario_sha256 = (Get-FileHash (Join-Path $root "scenarios/$scenario.json") -Algorithm SHA256).Hash
  domain_sha256 = (Get-FileHash (Join-Path $root 'src/Domain/Cancellation.cs') -Algorithm SHA256).Hash
  api_sha256 = (Get-FileHash (Join-Path $root 'src/Api/Program.cs') -Algorithm SHA256).Hash
  human = @{ prepare_min = $null; operate_min = $null; review_min = $null; rework_min = $null; wait_min = $null; note = '人工欄位由作者填；null＝未記錄，不是零' }
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $runDir 'manifest.json') -Encoding UTF8
Write-Host "run: $runId  status=$status  api_exit=$apiExit"
& python (Join-Path $root 'tools/check-load.py') $runDir
exit $LASTEXITCODE
