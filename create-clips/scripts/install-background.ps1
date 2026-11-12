<#
  install-background.ps1: make the processing script start by itself (opt-in, per user, no admin rights, fully removable).

  -Mode native   register the Chrome native-messaging host `com.createclips.processor` (HKCU registry key + a manifest file). The Twitch Chunk Recorder
                 then starts `cc.py watch` in the background when you press Record, and shows how many chunks are processed. Needs the extension loaded once
                 (its id is read from native-host\extension-id.txt in the extension folder, or pass -ExtensionId).
  -Mode task     a Scheduled Task that runs `cc.py watch` hidden at every logon (the watcher is then always on, even when Chrome is closed).
  -Mode both     native + task.
  -Mode remove   delete the registry key, the host manifest and the scheduled task.
  -Mode status   say what is installed and whether the watcher is running (changes nothing).
  -DryRun        print what would be written, write nothing.

  Examples (PowerShell):   .\install-background.ps1 -Mode status
                           .\install-background.ps1 -Mode native
                           .\install-background.ps1 -Mode remove
#>
param(
  [ValidateSet('native','task','both','remove','status')][string]$Mode = 'status',
  [string]$ExtensionId = '',
  [string]$ExtensionDir = 'C:\Users\Bulzart\Documents\twitch-chunk-recorder',
  [string]$Python = 'C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe',
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$cc      = 'C:\Users\Bulzart\.claude\create-clips'
$hostDir = Join-Path $cc 'native-host'
$name    = 'com.createclips.processor'
$manifest = Join-Path $hostDir "$name.json"
$launcher = Join-Path $hostDir 'native_host.bat'
$regKey  = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$name"
$taskName = 'CreateClipsWatcher'

function Say($m) { Write-Host $m }

function Get-ExtensionId {
  if ($ExtensionId) { return $ExtensionId.Trim() }
  $f = Join-Path $ExtensionDir 'native-host\extension-id.txt'
  if (Test-Path $f) { return (Get-Content $f -Raw).Trim() }
  throw "extension id unknown: pass -ExtensionId or make sure $f exists"
}

function Install-Native {
  $id = Get-ExtensionId
  if ($id -notmatch '^[a-p]{32}$') { throw "extension id '$id' is not a 32-letter a-p Chrome id" }
  $json = [ordered]@{
    name = $name; description = 'Create-clips processor link for the Twitch Chunk Recorder'
    path = $launcher; type = 'stdio'; allowed_origins = @("chrome-extension://$id/")
  } | ConvertTo-Json -Depth 4
  $bat = "@echo off`r`n`"$Python`" `"$cc\scripts\native_host.py`" %*`r`n"
  Say "host manifest : $manifest"
  Say "launcher      : $launcher"
  Say "registry key  : $regKey -> $manifest   (extension origin chrome-extension://$id/)"
  if ($DryRun) { return }
  New-Item -ItemType Directory -Force $hostDir | Out-Null
  [IO.File]::WriteAllText($manifest, $json, (New-Object Text.UTF8Encoding($false)))
  [IO.File]::WriteAllText($launcher, $bat, [Text.Encoding]::ASCII)
  New-Item -Path $regKey -Force | Out-Null
  Set-ItemProperty -Path $regKey -Name '(default)' -Value $manifest
  Say 'native host registered. Reload the extension (chrome://extensions) and press Record: the processor starts by itself.'
}

function Install-Task {
  $pythonw = $Python -replace 'python\.exe$', 'pythonw.exe'
  if (-not (Test-Path $pythonw)) { $pythonw = $Python }
  $arg = "`"$cc\scripts\cc.py`" watch"
  Say "scheduled task: $taskName at logon: $pythonw $arg"
  if ($DryRun) { return }
  $act  = New-ScheduledTaskAction -Execute $pythonw -Argument $arg -WorkingDirectory $cc
  $trg  = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $set  = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
  $prin = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $taskName -Action $act -Trigger $trg -Settings $set -Principal $prin -Force | Out-Null
  Say 'scheduled task registered (starts at the next logon; start it now with: Start-ScheduledTask CreateClipsWatcher).'
}

function Remove-All {
  Say "removing: $regKey, $manifest, $launcher, task $taskName"
  if ($DryRun) { return }
  if (Test-Path $regKey) { Remove-Item $regKey -Recurse -Force }
  foreach ($f in @($manifest, $launcher)) { if (Test-Path $f) { Remove-Item $f -Force } }
  if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false }
  Say 'removed.'
}

function Show-Status {
  Say ("native host key : " + $(if (Test-Path $regKey) { (Get-ItemProperty $regKey).'(default)' } else { 'not registered' }))
  Say ("host manifest   : " + $(if (Test-Path $manifest) { $manifest } else { 'absent' }))
  $t = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  Say ("scheduled task  : " + $(if ($t) { "$($t.State)" } else { 'not installed' }))
  $lock = 'C:\Users\Bulzart\Documents\stream-clips\runs\.watch.lock'
  $pid_ = 0
  if (Test-Path $lock) { [void][int]::TryParse((Get-Content $lock -Raw).Trim(), [ref]$pid_) }
  Say ("watcher         : " + $(if ($pid_ -gt 0 -and (Get-Process -Id $pid_ -ErrorAction SilentlyContinue)) { "running (pid $pid_)" } else { 'not running' }))
  $idf = Join-Path $ExtensionDir 'native-host\extension-id.txt'
  Say ("extension id    : " + $(if (Test-Path $idf) { (Get-Content $idf -Raw).Trim() } else { 'unknown (extension not built yet)' }))
}

switch ($Mode) {
  'native' { Install-Native }
  'task'   { Install-Task }
  'both'   { Install-Native; Install-Task }
  'remove' { Remove-All }
  'status' { Show-Status }
}
