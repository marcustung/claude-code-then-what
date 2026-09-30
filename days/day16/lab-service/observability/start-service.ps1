# 讓訂單服務「持續執行」，好讓容器裡的 Prometheus 定時抓 /metrics。
# 與 tools/run.ps1、tools/run-load.ps1 的差別只有兩點，其餘行為相同：
#   1) 綁 0.0.0.0 而非 127.0.0.1——容器經 host.docker.internal 連進來，連不到 loopback。
#   2) 起完就回，不跑負載、不匯出、不對帳、不停止服務。負載另外用 tools/load.py 打。
# 停止：observability/stop-service.ps1
#
#   powershell -NoProfile -File observability/start-service.ps1
#   powershell -NoProfile -File observability/start-service.ps1 -faults scenarios/faults/slow-sync-notify.json -sinkDelayMs 150
param(
  [string]$faults = '',
  [int]$sinkDelayMs = 0,
  [int]$apiPort = 5080,
  [int]$sinkPort = 5081,
  [switch]$noBuild
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$outDir = Join-Path $root 'observability/.run'
New-Item -ItemType Directory -Force $outDir | Out-Null

if (-not $noBuild) {
  foreach ($p in 'src/Domain/Domain.csproj', 'src/Api/Api.csproj', 'src/FakeSink/FakeSink.csproj') {
    $o = & dotnet build (Join-Path $root $p) -nologo -v q 2>&1
    if ($LASTEXITCODE -ne 0) { $o | Out-String | Write-Host; throw "build failed: $p" }
  }
}

foreach ($port in @($apiPort, $sinkPort)) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host "port $port busy (pid $($_.OwningProcess)) -> stop"; Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Milliseconds 300

function Start-Svc($proj, $envs, $tag) {
  $saved = @{}
  foreach ($k in $envs.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $envs[$k]) }
  try {
    $p = Start-Process -FilePath 'dotnet' -ArgumentList @('run', '--no-build', '--project', (Join-Path $root $proj)) `
      -WorkingDirectory $root -NoNewWindow -PassThru `
      -RedirectStandardOutput (Join-Path $outDir "$tag-stdout.txt") -RedirectStandardError (Join-Path $outDir "$tag-stderr.txt")
  } finally {
    foreach ($k in $envs.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) }
  }
  return $p
}

$sinkEnv = @{ OC_RUN_DIR = $outDir; ASPNETCORE_URLS = "http://0.0.0.0:$sinkPort" }
$apiEnv = @{ OC_RUN_DIR = $outDir; ASPNETCORE_URLS = "http://0.0.0.0:$apiPort"; OC_SINK_URL = "http://127.0.0.1:$sinkPort/notify" }
if ($sinkDelayMs -gt 0) { $apiEnv['OC_SINK_DELAY_MS'] = "$sinkDelayMs"; $sinkEnv['OC_SINK_DELAY_MS'] = "$sinkDelayMs" }
if ($faults) { $apiEnv['OC_FAULTS'] = (Join-Path $root $faults) }

$sink = Start-Svc 'src/FakeSink/FakeSink.csproj' $sinkEnv 'sink'
$api = Start-Svc 'src/Api/Api.csproj' $apiEnv 'api'
@{ api_pid = $api.Id; sink_pid = $sink.Id; faults = $faults; sink_delay_ms = $sinkDelayMs; started = (Get-Date).ToString('o') } |
  ConvertTo-Json | Set-Content (Join-Path $outDir 'service.json') -Encoding UTF8

$deadline = (Get-Date).AddSeconds(40)
while ((Get-Date) -lt $deadline) {
  try { if ((Invoke-WebRequest "http://127.0.0.1:$apiPort/metrics" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { break } } catch {}
  Start-Sleep -Milliseconds 300
}
Write-Host "api pid=$($api.Id) sink pid=$($sink.Id)  faults='$faults'  sink_delay=$sinkDelayMs ms"
Write-Host "metrics: http://127.0.0.1:$apiPort/metrics"
