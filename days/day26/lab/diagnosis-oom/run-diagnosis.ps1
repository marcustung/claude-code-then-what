# 盲診 runner：診斷者只看 snapshot/（無故障答案）。A 組 Read/Grep/Glob；B 組另掛 codegraph MCP（需先 codegraph init snapshot）。
#   powershell -NoProfile -File run-diagnosis.ps1 D1        （A 組）
#   powershell -NoProfile -File run-diagnosis.ps1 M1 -arm B （B 組）
param([string]$name = 'D1', [string]$arm = 'A')
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$utf8 = [Text.UTF8Encoding]::new($false)
$cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }
$root = $PSScriptRoot; $snap = Join-Path $root 'snapshot'
$out = Join-Path $root "runs\$name"; if (Test-Path (Join-Path $out 'trace.jsonl')) { throw "runs/$name 已存在" }; New-Item -ItemType Directory -Force $out | Out-Null
$prompt = [IO.File]::ReadAllText((Join-Path $root 'prompt.txt'), $utf8)
$tools = 'Read,Grep,Glob'
$args = "-p --model sonnet --effort low --strict-mcp-config --no-session-persistence --setting-sources `"`" --output-format stream-json --verbose"
if ($arm -eq 'B') {
  $cg = (Get-Command codegraph.cmd, codegraph -ErrorAction SilentlyContinue | Select-Object -First 1).Source
  $mcp = @{ mcpServers = @{ codegraph = @{ command = $cg; args = @('serve', '--mcp', '--no-watch', '--path', $snap) } } } | ConvertTo-Json -Depth 5
  $mcpPath = Join-Path $out 'mcp.json'; [IO.File]::WriteAllText($mcpPath, $mcp, $utf8)
  $cgTools = @('codegraph_explore','codegraph_search','codegraph_callers','codegraph_callees','codegraph_impact','codegraph_node','codegraph_files','codegraph_status') | ForEach-Object { "mcp__codegraph__$_" }
  $tools = ($cgTools + 'Read','Grep','Glob') -join ','
  $args += " --mcp-config `"$mcpPath`""
}
$args += " --tools $tools --allowedTools $tools"
$meta = @{ name = $name; arm = $arm; started_utc = (Get-Date).ToUniversalTime().ToString('o'); arguments = $args; cwd = $snap; prompt_sha256 = (Get-FileHash (Join-Path $root 'prompt.txt') -Algorithm SHA256).Hash }
$psi = [Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $cli; $psi.Arguments = $args; $psi.WorkingDirectory = $snap
$psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = $utf8; $psi.StandardErrorEncoding = $utf8
$proc = [Diagnostics.Process]::new(); $proc.StartInfo = $psi; $proc.Start() | Out-Null
$o = $proc.StandardOutput.ReadToEndAsync(); $e = $proc.StandardError.ReadToEndAsync()
$proc.StandardInput.Write($prompt); $proc.StandardInput.Close()
if (-not $proc.WaitForExit(420000)) { $proc.Kill(); throw 'timeout' }
$meta.exit_code = $proc.ExitCode; $meta.ended_utc = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText((Join-Path $out 'trace.jsonl'), $o.Result, $utf8)
[IO.File]::WriteAllText((Join-Path $out 'stderr.txt'), $e.Result, $utf8)
[IO.File]::WriteAllText((Join-Path $out 'meta.json'), ($meta | ConvertTo-Json), $utf8)
Write-Host "$name exit=$($meta.exit_code) bytes=$($o.Result.Length)"
