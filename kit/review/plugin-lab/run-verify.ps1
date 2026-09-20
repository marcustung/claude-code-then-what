# 2026-09-18 verification re-run of Day 4 claims. Writes to runs/verify-20260918/<name>; never touches the 09-15 runs.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot; $utf8 = [Text.UTF8Encoding]::new($false)
$cli = "$env:USERPROFILE\.local\bin\claude.exe"
$plugin = (Resolve-Path (Join-Path $root '..\plugin\review-kit')).Path
$plain = [IO.File]::ReadAllText((Join-Path $root 'runs\G0-A\prompt.txt'), $utf8)
$skill = [IO.File]::ReadAllText((Join-Path $root 'runs\S-A\prompt.txt'), $utf8)
function Run($name, $fixture, $prompt, $withPlugin) {
    $dir = Join-Path $root "runs\verify-20260918\$name"
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
    Copy-Item (Join-Path $root "fixtures\$fixture") $dir -Recurse
    [IO.File]::WriteAllText((Join-Path $dir 'prompt.txt'), $prompt, $utf8)
    $args = '-p --model sonnet --effort low --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --setting-sources "" '
    if ($withPlugin) { $args += "--plugin-dir `"$plugin`" --tools Read,Grep,Glob,Skill --allowedTools Read,Grep,Glob,Skill " } else { $args += '--tools Read,Grep,Glob --allowedTools Read,Grep,Glob ' }
    $start = [DateTime]::UtcNow
    $psi = [Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $cli; $psi.Arguments = $args; $psi.WorkingDirectory = $dir
    $psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $utf8; $psi.StandardErrorEncoding = $utf8
    $proc = [Diagnostics.Process]::new(); $proc.StartInfo = $psi; $proc.Start() | Out-Null
    $outTask = $proc.StandardOutput.ReadToEndAsync(); $errTask = $proc.StandardError.ReadToEndAsync()
    $proc.StandardInput.Write($prompt); $proc.StandardInput.Close()
    if (-not $proc.WaitForExit(300000)) { $proc.Kill(); throw "Timeout: $name" }
    [IO.File]::WriteAllText((Join-Path $dir 'trace.jsonl'), $outTask.Result, $utf8)
    [IO.File]::WriteAllText((Join-Path $dir 'stderr.txt'), $errTask.Result, $utf8)
    $meta = @{name=$name; fixture=$fixture; plugin=$withPlugin; started_utc=$start.ToString('o'); ended_utc=[DateTime]::UtcNow.ToString('o'); exit_code=$proc.ExitCode; arguments=$args; prompt_sha256=(Get-FileHash (Join-Path $dir 'prompt.txt')).Hash; purpose='2026-09-18 re-run to verify Day 4 text'}
    [IO.File]::WriteAllText((Join-Path $dir 'meta.json'), ($meta | ConvertTo-Json), $utf8)
    Write-Output "$name exit=$($proc.ExitCode)"
}
Run 'V-G0-A' 'pr-A' $plain $false
Run 'V-G0-B' 'pr-B' $plain $false
Run 'V-S-A'  'pr-A' $skill $true
