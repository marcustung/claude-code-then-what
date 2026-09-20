$ErrorActionPreference='Stop'
$utf8=[Text.UTF8Encoding]::new($false)
$rows=@()
# 公開版：run 目錄依天放在 days/dayNN/lab；本表由建置腳本產生
$RUNDIRS=@{'day02-write'='days/day02/lab';'day07'='days/day07/lab';'day07-r2'='days/day07/lab';'day07-r3'='days/day07/lab';'day09-A1'='days/day09/lab';'day09-B1'='days/day09/lab';'day09-B2'='days/day09/lab';'day09-A2'='days/day09/lab';'day09-A3'='days/day09/lab';'day09-B3'='days/day09/lab';'day10'='days/day10/lab';'day10-check'='days/day10/lab'}

foreach($name in @('day07','day09-A1','day09-B1','day09-B2','day09-A2','day09-A3','day09-B3','day10')) {
 $dir=Join-Path (Join-Path $PSScriptRoot '..\..') (Join-Path $RUNDIRS[$name] $name)
 $events=@(Get-Content -LiteralPath (Join-Path $dir 'trace.jsonl') -Encoding UTF8 | ForEach-Object { $_ | ConvertFrom-Json })
 $result=@($events | Where-Object type -eq 'result')[-1]
 if($result.is_error){throw "$name API error"}
 $raw=$result.result
 [IO.File]::WriteAllText((Join-Path $dir 'response.txt'),$raw,$utf8)
 $clean=$raw -replace '(?s)^\s*```(?:json)?\s*','' -replace '\s*```\s*$',''
 $answer=$clean | ConvertFrom-Json
 [IO.File]::WriteAllText((Join-Path $dir 'answer.json'),($answer | ConvertTo-Json -Depth 12),$utf8)
 $models=@($events | Where-Object type -eq 'assistant' | ForEach-Object {$_.message.model} | Select-Object -Unique)
 $tools=@($events | Where-Object type -eq 'assistant' | ForEach-Object {$_.message.content} | Where-Object type -eq 'tool_use')
 if($name -ne 'day10'){
  $expected=@($false,$false,$false,$true,$true)
  $hits=0
  if($answer.decisions.Count -eq 5){ for($i=0;$i -lt 5;$i++){if(($answer.decisions[$i] -is [bool]) -and $answer.decisions[$i] -eq $expected[$i]){$hits++}} }
  $rows += [pscustomobject]@{run=$name;models=$models;decisions_correct=$hits;rule_id=$answer.rule_id;marker=$answer.marker;tool_names=@($tools.name);bug=$answer.bug;unknowns=$answer.unknowns;reason_applied=$answer.reason_applied}
 }else{
  [IO.File]::WriteAllText((Join-Path $dir 'Guard.proposed.cs'),$answer.code,$utf8)
  $rows += [pscustomobject]@{run=$name;models=$models;explanation=$answer.explanation;tool_names=@($tools.name)}
 }
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'results.json'),($rows | ConvertTo-Json -Depth 12),$utf8)
$rows | ConvertTo-Json -Depth 12
