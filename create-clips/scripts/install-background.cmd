@echo off
rem Double-click to make the processing script start by itself (Chrome helper + logon task). Undo: uninstall-background.cmd
echo Registering the create-clips processing link for Chrome and the logon task (per user, no admin rights)...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-background.ps1" -Mode both
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-background.ps1" -Mode status
echo.
pause
