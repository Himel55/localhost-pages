# Register a Windows Scheduled Task that runs localhost-pages at user logon
# and restarts it if it exits. Run from the repo root in PowerShell:
#
#   powershell -ExecutionPolicy Bypass -File scripts\install-task.ps1
#
# Optional env overrides (set before running this script):
#   $env:LOCALHOST_PAGES_TASK = "my-task-name"
#   $env:LOCALHOST_PAGES_PORT = "80"

$ErrorActionPreference = "Stop"

$TaskName = if ($env:LOCALHOST_PAGES_TASK) { $env:LOCALHOST_PAGES_TASK } else { "localhost-pages" }
$Port     = if ($env:LOCALHOST_PAGES_PORT) { $env:LOCALHOST_PAGES_PORT } else { "8080" }
$ProjectDir = (Resolve-Path "$PSScriptRoot\..").Path

$UvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $UvPath) {
    Write-Error "'uv' not found on PATH. Install uv first: https://docs.astral.sh/uv/"
}

$LogDir = Join-Path $env:LOCALAPPDATA "localhost-pages"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogPath  = Join-Path $LogDir "localhost-pages.log"
$Launcher = Join-Path $LogDir "run.cmd"

# Write a tiny .cmd launcher. The Python app handles file logging via the
# LOCALHOST_PAGES_LOG env var, so we don't need cmd.exe stdout redirection.
@"
@echo off
set LOCALHOST_PAGES_LOG=$LogPath
set LOCALHOST_PAGES_PORT=$Port
"$UvPath" run --directory "$ProjectDir" python -m localhost_pages
"@ | Set-Content -Path $Launcher -Encoding ASCII

$Action    = New-ScheduledTaskAction    -Execute $Launcher -WorkingDirectory $ProjectDir
$Trigger   = New-ScheduledTaskTrigger   -AtLogOn -User $env:USERNAME
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$Settings  = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0)

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
    -TaskName  $TaskName `
    -Action    $Action `
    -Trigger   $Trigger `
    -Settings  $Settings `
    -Principal $Principal | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host "Registered scheduled task: $TaskName"
Write-Host "Launcher: $Launcher"
Write-Host "Logs:     $LogPath"
Write-Host "Stop:     Stop-ScheduledTask -TaskName $TaskName"
Write-Host "Remove:   Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
