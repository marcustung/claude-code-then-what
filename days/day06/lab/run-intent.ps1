$ErrorActionPreference='Stop'; $utf8=[Text.UTF8Encoding]::new($false); $cli="$env:USERPROFILE\.local\bin\claude.exe"
$dir=Join-Path $PSScriptRoot 'intent'; $p=[IO.File]::ReadAllText((Join-Path $dir 'prompt.txt'),$utf8)
$out=$dir; if(Test-Path (Join-Path $dir 'trace.jsonl')){ $out="$dir-rerun-$(Get-Date -Format yyyyMMdd-HHmmss)"; New-Item -ItemType Directory $out|Out-Null }  # 既有 run 不覆寫，重跑寫到新目錄
$args='-p --model sonnet --effort low --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --setting-sources "" --tools Read --allowedTools Read '
$start=[DateTime]::UtcNow; $psi=[Diagnostics.ProcessStartInfo]::new(); $psi.FileName=$cli; $psi.Arguments=$args; $psi.WorkingDirectory=$dir
$psi.UseShellExecute=$false; $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.StandardOutputEncoding=$utf8; $psi.StandardErrorEncoding=$utf8
$proc=[Diagnostics.Process]::new(); $proc.StartInfo=$psi; $proc.Start()|Out-Null; $o=$proc.StandardOutput.ReadToEndAsync(); $e=$proc.StandardError.ReadToEndAsync()
$proc.StandardInput.Write($p); $proc.StandardInput.Close(); if(-not $proc.WaitForExit(300000)){$proc.Kill(); throw 'timeout'}
[IO.File]::WriteAllText((Join-Path $out 'trace.jsonl'),$o.Result,$utf8); [IO.File]::WriteAllText((Join-Path $out 'stderr.txt'),$e.Result,$utf8)
@{name='intent';started_utc=$start.ToString('o');ended_utc=[DateTime]::UtcNow.ToString('o');exit_code=$proc.ExitCode;arguments=$args}|ConvertTo-Json|Set-Content (Join-Path $out 'meta.json') -Encoding UTF8
"intent exit=$($proc.ExitCode)"
