$ErrorActionPreference = 'Stop'
# Day 2 "write" run, 2026-09-12. Same protocol as run.ps1: sonnet, low effort, safe-mode, no tools, new session.
# Task: implement the guard from an under-specified ticket. Host compiles and runs the returned code.
$root = $PSScriptRoot
$utf8 = [Text.UTF8Encoding]::new($false)
$cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" } }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" }
$name = 'day02-write'
$dir = Join-Path $root $name
if (Test-Path (Join-Path $dir 'trace.jsonl')) { $dir = "$dir-rerun-$(Get-Date -Format yyyyMMdd-HHmmss)" }  # 既有 run 不覆寫
[IO.Directory]::CreateDirectory($dir) | Out-Null
$prompt = @'
You are implementing a public synthetic C# guard for a recruiting workflow. This is a teaching fixture, not a real company system.
Ticket text (this is all the requirement says): "A rejected candidate must not go directly back to Interviewing."
Current stub:
public static class Guard { public static bool CanEnterInterview(bool rejected, bool reopenRequested, bool authorized) => throw new NotImplementedException(); }
Implement the guard and write a minimal console test. Return ONLY JSON with keys:
  code   - complete compilable Guard.cs source (preserve class name and signature, no dependencies, no I/O)
  test   - complete compilable Program.cs top-level-statements source that calls Guard.CanEnterInterview, prints PASS/FAIL per case, and returns exit 0 when all pass
  explanation - what you implemented
  assumptions - list every business rule you assumed that the ticket text does not state
No tools are available. Do not claim to execute anything. The host will compile and run your returned code.
'@
[IO.File]::WriteAllText((Join-Path $dir 'prompt.txt'), $prompt, $utf8)
$start = [DateTime]::UtcNow
$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $cli
$psi.Arguments = '-p --model sonnet --effort low --safe-mode --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --tools ""'
$psi.WorkingDirectory = $dir
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = $utf8
$psi.StandardErrorEncoding = $utf8
$proc = [Diagnostics.Process]::new()
$proc.StartInfo = $psi
$proc.Start() | Out-Null
$outTask = $proc.StandardOutput.ReadToEndAsync()
$errTask = $proc.StandardError.ReadToEndAsync()
$proc.StandardInput.Write($prompt)
$proc.StandardInput.Close()
if (-not $proc.WaitForExit(240000)) { $proc.Kill(); throw "Timeout: $name" }
[IO.File]::WriteAllText((Join-Path $dir 'trace.jsonl'), $outTask.Result, $utf8)
[IO.File]::WriteAllText((Join-Path $dir 'stderr.txt'), $errTask.Result, $utf8)
$meta = @{name=$name;started_utc=$start.ToString('o');ended_utc=[DateTime]::UtcNow.ToString('o');exit_code=$proc.ExitCode;arguments=$psi.Arguments;prompt_sha256=(Get-FileHash (Join-Path $dir 'prompt.txt')).Hash}
[IO.File]::WriteAllText((Join-Path $dir 'meta.json'), ($meta | ConvertTo-Json), $utf8)
Write-Output "$name exit=$($proc.ExitCode)"
if ($proc.ExitCode -ne 0) { throw "Claude failed: $name; inspect trace and stderr" }
