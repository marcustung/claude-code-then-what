# 2026-09-19: repeat the Day 7 read-card run twice (day07-r2, day07-r3) with identical prompt/card/flags. Originals untouched.
$ErrorActionPreference='Stop'; $utf8=[Text.UTF8Encoding]::new($false); $cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" } }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" }
$prompt=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'day07\prompt.txt'),$utf8)
foreach($name in @('day07-r2','day07-r3')){
  $dir=Join-Path $PSScriptRoot $name; if(Test-Path $dir){ $dir="$dir-rerun-$(Get-Date -Format yyyyMMdd-HHmmss)" }  # 既有 run 不覆寫
  New-Item -ItemType Directory $dir|Out-Null
  Copy-Item (Join-Path $PSScriptRoot 'rule-card.md') $dir; [IO.File]::WriteAllText((Join-Path $dir 'prompt.txt'),$prompt,$utf8)
  $args='-p --model sonnet --effort low --safe-mode --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --tools Read --allowedTools Read'
  $start=[DateTime]::UtcNow; $psi=[Diagnostics.ProcessStartInfo]::new(); $psi.FileName=$cli; $psi.Arguments=$args; $psi.WorkingDirectory=$dir
  $psi.UseShellExecute=$false; $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.StandardOutputEncoding=$utf8; $psi.StandardErrorEncoding=$utf8
  $proc=[Diagnostics.Process]::new(); $proc.StartInfo=$psi; $proc.Start()|Out-Null; $o=$proc.StandardOutput.ReadToEndAsync(); $e=$proc.StandardError.ReadToEndAsync()
  $proc.StandardInput.Write($prompt); $proc.StandardInput.Close(); if(-not $proc.WaitForExit(300000)){$proc.Kill(); throw "timeout $name"}
  [IO.File]::WriteAllText((Join-Path $dir 'trace.jsonl'),$o.Result,$utf8); [IO.File]::WriteAllText((Join-Path $dir 'stderr.txt'),$e.Result,$utf8)
  @{name=$name;started_utc=$start.ToString('o');ended_utc=[DateTime]::UtcNow.ToString('o');exit_code=$proc.ExitCode;arguments=$args;purpose='2026-09-19 repeat of day07 for stability'}|ConvertTo-Json|Set-Content (Join-Path $dir 'meta.json') -Encoding UTF8
  "$name exit=$($proc.ExitCode)"
}
