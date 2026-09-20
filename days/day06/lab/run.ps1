$ErrorActionPreference='Stop'; $utf8=[Text.UTF8Encoding]::new($false); $cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = (Get-Command claude.exe, claude.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $cli) { $cli = "$env:USERPROFILE\.local\bin\claude.exe" }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" } }; if (-not (Test-Path $cli)) { throw "找不到 Claude Code CLI：請先安裝並登入（npm i -g @anthropic-ai/claude-code 或官方安裝器），再重跑" }
function Run($sub,$tools){ $dir=Join-Path $PSScriptRoot $sub; $p=[IO.File]::ReadAllText((Join-Path $dir 'prompt.txt'),$utf8)
$out=$dir; if(Test-Path (Join-Path $dir 'trace.jsonl')){ $out="$dir-rerun-$(Get-Date -Format yyyyMMdd-HHmmss)"; New-Item -ItemType Directory $out|Out-Null }  # 既有 run 不覆寫，重跑寫到新目錄
  $args="-p --model sonnet --effort low --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --setting-sources `"`" --tools $tools --allowedTools $tools --permission-mode bypassPermissions "
  $start=[DateTime]::UtcNow; $psi=[Diagnostics.ProcessStartInfo]::new(); $psi.FileName=$cli; $psi.Arguments=$args; $psi.WorkingDirectory=$dir
  $psi.UseShellExecute=$false; $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.StandardOutputEncoding=$utf8; $psi.StandardErrorEncoding=$utf8
  $proc=[Diagnostics.Process]::new(); $proc.StartInfo=$psi; $proc.Start()|Out-Null; $o=$proc.StandardOutput.ReadToEndAsync(); $e=$proc.StandardError.ReadToEndAsync()
  $proc.StandardInput.Write($p); $proc.StandardInput.Close(); if(-not $proc.WaitForExit(420000)){$proc.Kill(); throw "timeout $sub"}
  [IO.File]::WriteAllText((Join-Path $out 'trace.jsonl'),$o.Result,$utf8); [IO.File]::WriteAllText((Join-Path $out 'stderr.txt'),$e.Result,$utf8)
  @{name=$sub;started_utc=$start.ToString('o');ended_utc=[DateTime]::UtcNow.ToString('o');exit_code=$proc.ExitCode;arguments=$args}|ConvertTo-Json|Set-Content (Join-Path $out 'meta.json') -Encoding UTF8
  Write-Output "$sub exit=$($proc.ExitCode)" }
Run 'draft' 'Read,Grep,Glob'
Run 'impl'  'Read,Grep,Glob,Write,Edit,Bash'
