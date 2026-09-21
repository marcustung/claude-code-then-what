# Day 8 引用抽驗實驗 runner。用法：powershell -NoProfile -File run.ps1 r1
param([string]$name = 'r1', [string]$tools = 'Read,Grep,Glob', [string]$promptFile = 'prompt.txt')
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$utf8 = [Text.UTF8Encoding]::new($false)
$cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" }
$root = $PSScriptRoot
$out = Join-Path $root "runs\$name"; if (Test-Path (Join-Path $out 'trace.jsonl')) { throw "runs/$name 已存在，換一個名字；既有 run 不覆寫" }; New-Item -ItemType Directory -Force $out | Out-Null
$prompt = [IO.File]::ReadAllText((Join-Path $root $promptFile), $utf8)
$toolArg = if ($tools -eq '') { '--tools ""' } else { "--tools $tools --allowedTools $tools" }
$args = "-p --model sonnet --effort low --strict-mcp-config --no-session-persistence --setting-sources `"`" --output-format stream-json --verbose $toolArg"
$meta = @{ name = $name; started_utc = (Get-Date).ToUniversalTime().ToString('o'); arguments = $args; cwd = (Join-Path $root 'repo'); prompt_sha256 = (Get-FileHash (Join-Path $root $promptFile) -Algorithm SHA256).Hash }
$psi = [Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $cli; $psi.Arguments = $args; $psi.WorkingDirectory = (Join-Path $root 'repo')
$psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = $utf8; $psi.StandardErrorEncoding = $utf8
$proc = [Diagnostics.Process]::new(); $proc.StartInfo = $psi; $proc.Start() | Out-Null
$o = $proc.StandardOutput.ReadToEndAsync(); $e = $proc.StandardError.ReadToEndAsync()
$proc.StandardInput.Write($prompt); $proc.StandardInput.Close()
if (-not $proc.WaitForExit(300000)) { $proc.Kill(); throw 'timeout' }
$stdout = $o.Result; $stderr = $e.Result; $meta.exit_code = $proc.ExitCode
$meta.ended_utc = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText((Join-Path $out 'trace.jsonl'), $stdout, $utf8)
[IO.File]::WriteAllText((Join-Path $out 'stderr.txt'), $stderr, $utf8)
[IO.File]::WriteAllText((Join-Path $out 'meta.json'), ($meta | ConvertTo-Json), $utf8)
Write-Host "$name exit=$($meta.exit_code) bytes=$($stdout.Length)"
