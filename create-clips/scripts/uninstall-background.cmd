@echo off
rem Double-click to remove what install-background.cmd added (registry key, host files, logon task).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-background.ps1" -Mode remove
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-background.ps1" -Mode status
echo.
pause
