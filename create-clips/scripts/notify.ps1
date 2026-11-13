# create-clips: show one Windows notification (a toast) from a JSON payload.
#
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File notify.ps1 -PayloadFile <payload.json> [-DryRun]
#
# payload: {"title": "...", "lines": ["...", "..."], "persistent": true, "sound": true}
# Prints ONE JSON line: {"ok": true, "how": "toast"|"dry-run", "setting": "Enabled", ...} or {"ok": false, "error": "..."}.
# -DryRun builds the toast and asks Windows whether notifications are enabled, but shows nothing.
#
# Needs Windows PowerShell 5.1 (powershell.exe): the toast classes are Windows Runtime types, loaded with the syntax below only there.
# The toast goes out under the registered app id of Windows PowerShell, so nothing is registered or changed on this PC.
# When the toast cannot be shown (notifications off for that app, no Windows Runtime), cc_notify.py shows a message box instead.
# ASCII only: PowerShell 5.1 reads a script without a byte-order mark as ANSI.
param(
    [Parameter(Mandatory = $true)][string]$PayloadFile,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'

function Write-Result($obj) {
    [Console]::Out.WriteLine(($obj | ConvertTo-Json -Compress -Depth 5))
}

try {
    $p = Get-Content -LiteralPath $PayloadFile -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-Result @{ ok = $false; error = ('payload not readable: ' + $_.Exception.Message) }
    exit 1
}
$title = [string]$p.title
$lines = @($p.lines | ForEach-Object { [string]$_ })
$persistent = [bool]$p.persistent
$sound = [bool]$p.sound

function Esc([string]$s) { [System.Security.SecurityElement]::Escape($s) }

# Windows Runtime's own answer (the notifier's Setting property) does not come through in PowerShell 5.1, so the two switches the user can turn
# are read from the registry: "notifications" in Settings (all apps) and the entry of this app. Nothing is written.
function Get-ToastSetting([string]$appId) {
    try {
        $g = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\PushNotifications' -Name ToastEnabled -ErrorAction Stop
        if ($g.ToastEnabled -eq 0) { return 'DisabledForUser' }
    } catch { }
    foreach ($name in @($appId, $appId.Replace('\', '.'))) {
        try {
            $a = Get-ItemProperty -LiteralPath ('Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\' + $name) -Name Enabled -ErrorAction Stop
            if ($a.Enabled -eq 0) { return 'DisabledForApplication' }
        } catch { }
    }
    return 'Enabled'
}

$body = '<text>' + (Esc $title) + '</text>'
foreach ($l in $lines) { $body += '<text>' + (Esc $l) + '</text>' }
if ($persistent) {
    # a reminder stays on screen until it is dismissed (it needs a button: a system "dismiss" needs no code behind it)
    $open = '<toast scenario="reminder">'
    $actions = '<actions><action content="Dismiss" arguments="dismiss" activationType="system"/></actions>'
} else {
    $open = '<toast duration="long">'
    $actions = ''
}
if ($sound) { $audio = '<audio src="ms-winsoundevent:Notification.Reminder"/>' } else { $audio = '<audio silent="true"/>' }
$xml = $open + '<visual><binding template="ToastGeneric">' + $body + '</binding></visual>' + $audio + $actions + '</toast>'

try {
    [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
    $doc = New-Object Windows.Data.Xml.Dom.XmlDocument
    $doc.LoadXml($xml)
    $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId)
    $setting = Get-ToastSetting $appId
    if ($DryRun) {
        Write-Result @{ ok = ($setting -eq 'Enabled'); how = 'dry-run'; setting = $setting; xml = $xml }
        exit 0
    }
    if ($setting -ne 'Enabled') {
        Write-Result @{ ok = $false; setting = $setting; error = ('notifications are not enabled for this app (' + $setting + ')') }
        exit 2
    }
    $toast = New-Object Windows.UI.Notifications.ToastNotification $doc
    $notifier.Show($toast)
    Write-Result @{ ok = $true; how = 'toast'; setting = $setting }
    exit 0
} catch {
    Write-Result @{ ok = $false; error = $_.Exception.Message }
    exit 1
}
