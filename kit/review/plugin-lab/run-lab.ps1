# Day 4 lab: does the review-pr skill add anything over a plain review? G0 = no plugin; S = plugin loaded via --plugin-dir.
# A = PR without rule sources (should be OWNER_REQUIRED / NEEDS_EVIDENCE); B = PR with Owner-confirmed rules (should PASS or at most ask).
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$utf8 = [Text.UTF8Encoding]::new($false)
$cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" } }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" }
$plugin = (Resolve-Path (Join-Path $root '..\plugin\review-kit')).Path
$plain = @'
Review the pull request in the current directory. Files: PR.md (author's description), ticket.md (requirement), diff.patch (the change), Program.cs (tests). Read only; do not modify or run anything.
Reply with ONE JSON object and nothing else: {"verdict": "PASS"|"NEEDS_EVIDENCE"|"OWNER_REQUIRED", "findings": [{"claim": "...", "source": "file:line or quote", "missing": "...", "severity": "block|ask|note"}], "owner_questions": ["..."]}
'@
$skill = @'
Use the review-kit:review-pr skill (invoke it with the Skill tool) to review the pull request in the current directory. Files: PR.md, ticket.md, diff.patch, Program.cs. Follow the skill's output format exactly: reply with ONE JSON object and nothing else.
'@
function Run($name, $fixture, $prompt, $withPlugin) {
    $dir = Join-Path $root "runs\$name"
    if (Test-Path $dir) { $dir = "$dir-rerun-$(Get-Date -Format yyyyMMdd-HHmmss)" }  # 既有 run 不覆寫
    Copy-Item (Join-Path $root "fixtures\$fixture") $dir -Recurse
    $p = $prompt -replace "`r`n", "`n"
    [IO.File]::WriteAllText((Join-Path $dir 'prompt.txt'), $p, $utf8)
    $args = '-p --model sonnet --effort low --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --setting-sources "" '
    if ($withPlugin) { $args += "--plugin-dir `"$plugin`" --tools Read,Grep,Glob,Skill --allowedTools Read,Grep,Glob,Skill " } else { $args += '--tools Read,Grep,Glob --allowedTools Read,Grep,Glob ' }
    $start = [DateTime]::UtcNow
    $psi = [Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $cli; $psi.Arguments = $args; $psi.WorkingDirectory = $dir
    $psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $utf8; $psi.StandardErrorEncoding = $utf8
    $proc = [Diagnostics.Process]::new(); $proc.StartInfo = $psi; $proc.Start() | Out-Null
    $outTask = $proc.StandardOutput.ReadToEndAsync(); $errTask = $proc.StandardError.ReadToEndAsync()
    $proc.StandardInput.Write($p); $proc.StandardInput.Close()
    if (-not $proc.WaitForExit(300000)) { $proc.Kill(); throw "Timeout: $name" }
    [IO.File]::WriteAllText((Join-Path $dir 'trace.jsonl'), $outTask.Result, $utf8)
    [IO.File]::WriteAllText((Join-Path $dir 'stderr.txt'), $errTask.Result, $utf8)
    $meta = @{name=$name; fixture=$fixture; plugin=$withPlugin; started_utc=$start.ToString('o'); ended_utc=[DateTime]::UtcNow.ToString('o'); exit_code=$proc.ExitCode; arguments=$args; prompt_sha256=(Get-FileHash (Join-Path $dir 'prompt.txt')).Hash}
    [IO.File]::WriteAllText((Join-Path $dir 'meta.json'), ($meta | ConvertTo-Json), $utf8)
    Write-Output "$name exit=$($proc.ExitCode)"
}
# round 1 (2026-09-15): G0-A, S-A, S-B, G0-B. G0-B caught that fixtures/pr-B/ticket.md was still v1 while PR.md claimed v2 (fixture defect);
# runs/round1/ keeps S-B and G0-B from that round. ticket.md fixed to v2, then S-B and G0-B re-run as round 2.
$which = if ($args.Count) { $args } else { @('G0-A','S-A','S-B','G0-B') }
if ($which -contains 'G0-A') { Run 'G0-A' 'pr-A' $plain $false }
if ($which -contains 'S-A')  { Run 'S-A'  'pr-A' $skill $true }
if ($which -contains 'S-B')  { Run 'S-B'  'pr-B' $skill $true }
if ($which -contains 'G0-B') { Run 'G0-B' 'pr-B' $plain $false }
