<#
  install-background.ps1: make the processing script start by itself (opt-in, per user, no admin rights, fully removable).

  -Mode native   register the Chrome native-messaging host `com.createclips.processor` (HKCU registry key + a manifest file). The Twitch Chunk Recorder
                 then starts `cc.py watch` in the background when you press Record, and shows how many chunks are processed. The extension's id is the
                 same on every PC (its manifest.json carries a fixed key): it is read from native-host\extension-id.txt in -ExtensionDir when you pass
                 that folder, from -ExtensionId when you pass it, and is otherwise the id built into this script.
  -Mode task     a Scheduled Task that runs `cc.py watch` hidden at every logon (the watcher is then always on, even when Chrome is closed).
  -Mode both     native + task.
  -Mode remove   delete the registry key, the host manifest and the scheduled task.
  -Mode status   say what is installed and whether the watcher is running (changes nothing).
  -DryRun        print what would be written, write nothing.
  -Python        the python.exe to start the host and the watcher with (default: the Python 3.12 found on this PC).

  Works from wherever the create-clips folder is (it uses its own location). Both the host and the watcher need CC_SOURCE_KEY in their environment
  (the toolkit's code is encrypted at rest): set it with setx and start Chrome / log on again afterwards.

  Examples (PowerShell):   .\install-background.ps1 -Mode status
                           .\install-background.ps1 -Mode native
                           .\install-background.ps1 -Mode remove
#>
param(
  [ValidateSet('native','task','both','remove','status')][string]$Mode = 'status',
  [string]$ExtensionId = '',
  [string]$ExtensionDir = '',
  [string]$Python = '',
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$cc      = Split-Path $PSScriptRoot -Parent            # the create-clips folder this script sits in (scripts\..)
$hostDir = Join-Path $cc 'native-host'
$name    = 'com.createclips.processor'
$manifest = Join-Path $hostDir "$name.json"
$launcher = Join-Path $hostDir 'native_host.bat'
$regKey  = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$name"
$taskName = 'CreateClipsWatcher'
$PinnedId = 'clnbfkmjckffkfgnhnfacicbalpieddp'          # the id of the Twitch Chunk Recorder (fixed by the "key" in its manifest.json)

function Say($m) { Write-Host $m }

function Find-Python {
  foreach ($cmd in @(@('py','-3.12'), @('python'))) {
    try {
      $exe = (Get-Command $cmd[0] -ErrorAction Stop).Source
      $pyArgs = @($cmd | Select-Object -Skip 1) + @('-c','import sys; print(sys.executable)')
      $p = (& $exe @pyArgs 2>$null | Select-Object -First 1)
      if ($p -and (Test-Path $p.Trim())) { return $p.Trim() }
    } catch { }
  }
  throw 'python.exe not found: install Python 3.12 or pass -Python <full path to python.exe>'
}
if ($Mode -in @('native','task','both') -and -not $Python) { $Python = Find-Python }

function Get-ExtensionId {
  if ($ExtensionId) { return $ExtensionId.Trim() }
  if ($ExtensionDir) {
    $f = Join-Path $ExtensionDir 'native-host\extension-id.txt'
    if (Test-Path $f) { return (Get-Content $f -Raw).Trim() }
  }
  return $PinnedId
}

function Get-RunsRoot {
  if ($env:CC_RUNS_ROOT) { return $env:CC_RUNS_ROOT }
  try { $r = (Get-Content (Join-Path $cc 'config.json') -Raw | ConvertFrom-Json).runs_root; if ($r) { return $r } } catch { }
  return (Join-Path $cc 'runs')
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
  Say 'Chrome gives the host its own environment: if you set CC_SOURCE_KEY after Chrome started, close every Chrome window (and its background process) and open it again.'
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
  $lock = Join-Path (Get-RunsRoot) '.watch.lock'
  $pid_ = 0
  if (Test-Path $lock) { [void][int]::TryParse((Get-Content $lock -Raw).Trim(), [ref]$pid_) }
  Say ("watcher         : " + $(if ($pid_ -gt 0 -and (Get-Process -Id $pid_ -ErrorAction SilentlyContinue)) { "running (pid $pid_)" } else { 'not running' }))
  Say ("extension id    : " + (Get-ExtensionId))
}

switch ($Mode) {
  'native' { Install-Native }
  'task'   { Install-Task }
  'both'   { Install-Native; Install-Task }
  'remove' { Remove-All }
  'status' { Show-Status }
}
