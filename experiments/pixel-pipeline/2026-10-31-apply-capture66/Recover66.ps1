$ErrorActionPreference='Stop'
$taskRoot='C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66'
$project='C:\Users\15352\Documents\work\Fantasy Survival Escape Game'
$targetProcessId=28304
$expectedExe='C:\Users\15352\Documents\work\6000.5.9f1\Editor\Unity.exe'
$expectedStarted=[DateTime]::Parse('2026-10-31T07:03:39.720934Z').ToUniversalTime()
$marker=Join-Path $taskRoot 'RECOVERY_STARTED66.json'
if(Test-Path -LiteralPath $marker){throw 'Recovery marker exists. Inspect actual outcome; do not repeat.'}
function Sha([string]$path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function SaveEvidence([string]$name,$value){$value|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $taskRoot $name) -Encoding utf8}
$backup=Get-Content -LiteralPath (Join-Path $taskRoot 'BACKUP66.json') -Raw|ConvertFrom-Json
$plan=Get-Content -LiteralPath (Join-Path $taskRoot 'BACKUP_PLAN66.json') -Raw|ConvertFrom-Json
foreach($entry in $backup.disk){if((Sha(Join-Path (Join-Path $taskRoot 'backup\disk') $entry.path)) -ne $entry.sha256){throw "Backup mismatch: $($entry.path)"}}
foreach($entry in $plan.files){if((Sha(Join-Path $project $entry.path)) -ne $entry.sha256){throw "Protected source changed: $($entry.path)"}}
foreach($entry in $backup.native){
 if($entry.nativeSnapshot){if((Sha(Join-Path (Join-Path $taskRoot 'backup\serialized') ($entry.path+'.json'))) -ne $entry.jsonSHA256){throw 'Serialized backup mismatch'}}
 if($entry.publicMeshSHA256){if((Sha(Join-Path $taskRoot 'backup\mesh-readable66.bin')) -ne $entry.publicMeshSHA256){throw 'Mesh backup mismatch'}}
}
$p=Get-CimInstance Win32_Process -Filter "ProcessId=$targetProcessId"
if(-not $p){throw 'Original Unity PID already absent; inspect current instances before restart.'}
$match=[regex]::Match($p.CommandLine,'(?i)-projectpath\s+"([^"]+)"')
if(-not $match.Success -or $match.Groups[1].Value -ne $project -or $p.ExecutablePath -ne $expectedExe){throw 'PID/project/executable mismatch; no process action.'}
if([Math]::Abs(($p.CreationDate.ToUniversalTime()-$expectedStarted).TotalSeconds) -gt 1){throw 'Process creation time changed; PID may be reused.'}
$process=Get-Process -Id $targetProcessId
$before=@{utc=[DateTime]::UtcNow.ToString('O');pid=$targetProcessId;project=$project;executable=$p.ExecutablePath;startedUTC=$p.CreationDate.ToUniversalTime().ToString('O');cpuSeconds=$process.CPU;workingSetBytes=$process.WorkingSet64;saveReportPresent=(Test-Path -LiteralPath (Join-Path $taskRoot 'SAVE66.json'));responding=$process.Responding;protected110Verified=$true;native5AndMeshBackupVerified=$true}
SaveEvidence 'RECOVERY_PREFLIGHT66.json' $before
if($before.saveReportPresent -or $before.responding){SaveEvidence 'RECOVERY_STOPPED66.json' @{reason='Possible recovery: no termination requested';state=$before};$before|ConvertTo-Json -Compress;exit}
SaveEvidence 'RECOVERY_STARTED66.json' @{utc=[DateTime]::UtcNow.ToString('O');targetPID=$targetProcessId;project=$project;scope='Only this confirmed frozen Unity; no children/other apps/library/assets touched'}
$normalClose=$process.CloseMainWindow()
SaveEvidence 'NORMAL_CLOSE66.json' @{utc=[DateTime]::UtcNow.ToString('O');pid=$targetProcessId;closeRequestPosted=$normalClose}
$normalExited=$process.WaitForExit(8000)
$forced=$false
if(-not $normalExited){
 $again=Get-CimInstance Win32_Process -Filter "ProcessId=$targetProcessId"
 if($again -and $again.ExecutablePath -eq $expectedExe -and [Math]::Abs(($again.CreationDate.ToUniversalTime()-$expectedStarted).TotalSeconds) -lt 1){Stop-Process -Id $targetProcessId -Force -ErrorAction Stop;$forced=$true}
 Start-Sleep -Seconds 1
}
if(Get-CimInstance Win32_Process -Filter "ProcessId=$targetProcessId"){throw 'Original target still present; do not start duplicate.'}
SaveEvidence 'UNITY_EXIT66.json' @{utc=[DateTime]::UtcNow.ToString('O');pid=$targetProcessId;normalExited=$normalExited;forced=$forced;childProcessesTargeted=$false}
$sameProject=@(Get-CimInstance Win32_Process -Filter "Name='Unity.exe'"|Where-Object {$m=[regex]::Match($_.CommandLine,'(?i)-projectpath\s+"([^"]+)"');$m.Success -and $m.Groups[1].Value -eq $project})
if($sameProject.Count -gt 0){SaveEvidence 'RESTART_SKIPPED66.json' @{reason='Another same-project Unity already exists';pids=@($sameProject.ProcessId)};throw 'Do not start duplicate project instance.'}
$log=Join-Path $taskRoot 'RECOVERY_EDITOR66.log'
SaveEvidence 'RESTART_REQUEST66.json' @{utc=[DateTime]::UtcNow.ToString('O');exe=$expectedExe;project=$project;log=$log}
$new=Start-Process -FilePath $expectedExe -ArgumentList @('-projectPath',('"'+$project+'"'),'-logFile',('"'+$log+'"')) -PassThru
$started=@{utc=[DateTime]::UtcNow.ToString('O');newPID=$new.Id;project=$project;exe=$expectedExe;log=$log;forcedOldPIDOnly=$forced;noAssetsOrLibraryModifiedByScript=$true}
SaveEvidence 'UNITY_RESTARTED66.json' $started
$started|ConvertTo-Json -Compress
