# Day 4 驗證重跑：三個條件（V-G0-A 純提示、V-G0-B 純提示 pr-B、V-S-A 載入 plugin），每次寫到 runs/verify-<時間戳>/<name>，不覆寫任何歷史 run。
# 歷史結果在公開 repo 的 days/day04/lab-plugin/verify-20260918 與 days/day05/lab/V-G0-A，跑完拿來對照。
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot; $utf8 = [Text.UTF8Encoding]::new($false)
$cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" }
$plugin = (Resolve-Path (Join-Path $root '..\plugin\review-kit')).Path
$plain = [IO.File]::ReadAllText((Join-Path $root 'prompts\plain.txt'), $utf8)
$skill = [IO.File]::ReadAllText((Join-Path $root 'prompts\skill.txt'), $utf8)
$stamp = Get-Date -Format yyyyMMdd-HHmmss
function Run($name, $fixture, $prompt, $withPlugin) {
    $dir = Join-Path $root "runs\verify-$stamp\$name"
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

# 跑完直接抽 JSON 並用 R1–R5 程式驗（需要 Python 3；沒有就手動：python extract_result.py <run>; python check_card.py <run>）
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($py) {
  Push-Location $root
  foreach ($n in @('V-G0-A','V-G0-B','V-S-A')) {
    $r = "runs\verify-$stamp\$n"
    & $py extract_result.py $r | Out-Null
    & $py check_card.py $r
  }
  Pop-Location
  "對照歷史結果：days/day04/lab-plugin/verify-20260918（V-G0-B、V-S-A）與 days/day05/lab/V-G0-A 各自的 check.json"
} else { "沒有 python，略過 extract／check；裝好後手動執行 extract_result.py 與 check_card.py" }
