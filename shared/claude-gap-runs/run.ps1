$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$utf8 = [Text.UTF8Encoding]::new($false)
$cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" } }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" }
function Run-Claude($name, $prompt, $readFiles) {
    $dir = Join-Path $root $name
    [IO.Directory]::CreateDirectory($dir) | Out-Null
    [IO.File]::WriteAllText((Join-Path $dir 'prompt.txt'), $prompt, $utf8)
    if ($readFiles) { Copy-Item (Join-Path $root 'rule-card.md') (Join-Path $dir 'rule-card.md') }
    $start = [DateTime]::UtcNow
    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $cli
    $toolArgs = if ($readFiles) { '--tools Read --allowedTools Read' } else { '--tools ""' }
    $psi.Arguments = '-p --model sonnet --effort low --safe-mode --strict-mcp-config --no-session-persistence --output-format stream-json --verbose ' + $toolArgs
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
    $stdout = $outTask.Result
    [IO.File]::WriteAllText((Join-Path $dir 'trace.jsonl'), $stdout, $utf8)
    [IO.File]::WriteAllText((Join-Path $dir 'stderr.txt'), $errTask.Result, $utf8)
    $meta = @{name=$name;started_utc=$start.ToString('o');ended_utc=[DateTime]::UtcNow.ToString('o');exit_code=$proc.ExitCode;arguments=$psi.Arguments;prompt_sha256=(Get-FileHash (Join-Path $dir 'prompt.txt')).Hash}
    [IO.File]::WriteAllText((Join-Path $dir 'meta.json'), ($meta | ConvertTo-Json), $utf8)
    Write-Output "$name exit=$($proc.ExitCode)"
    if ($proc.ExitCode -ne 0) { throw "Claude failed: $name; inspect trace and stderr" }
}

Run-Claude 'day07' 'Read rule-card.md with the Read tool. Return ONLY JSON with keys marker, rule_id, decisions (boolean array in input order), reason_applied, unknowns. Inputs (rejected,reopenRequested,authorized): (true,false,false),(true,true,false),(true,false,true),(true,true,true),(false,false,false). Explain briefly how the reason affects your decision. Do not inspect any other files.' $true
$common = 'Evaluate this synthetic guard, not a real company system. Proposed C#: return !rejected; Inputs (rejected,reopenRequested,authorized): (true,false,false),(true,true,false),(true,false,true),(true,true,true),(false,false,false). Rule RULE-01: direct return from rejected is forbidden; explicit authorized reopening is allowed. Non-rejected states are outside this guard. Return ONLY JSON: {"decisions":[booleans in input order],"rule_id":"...","bug":"...","unknowns":[...]}. Do not invent system rules.'
$reason = ' Reason: direct return bypasses the rejection decision; explicit authorized reopening records a deliberate exception.'
foreach ($run in @('A1','B1','B2','A2','A3','B3')) {
    $prompt = if ($run.StartsWith('B')) { $common + $reason } else { $common }
    Run-Claude ('day09-' + $run) $prompt $false
}
$repair = @'
Repair this public synthetic C# guard. Return ONLY JSON with keys code (complete compilable Guard.cs source), explanation, tests_to_run. Do not claim to execute anything. No tools are available.
Current Guard.cs:
public static class Guard { public static bool CanEnterInterview(bool rejected, bool reopenRequested, bool authorized) => !rejected; }
RULE-01: direct return from rejected is forbidden. Explicit authorized reopening is allowed only when BOTH reopenRequested and authorized are true. Non-rejected states are outside this guard. Preserve class and signature. Do not add dependencies, I/O, API, auth systems or unrelated changes. Host will compile your returned code and run independent checks.
'@
Run-Claude 'day10' $repair $false
