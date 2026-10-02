@echo off
title Uninstall CrewAI Auto-Run
cd /d "%~dp0"
set "STARTUP_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CrewAI RAG AutoRun.lnk"
if exist "%STARTUP_LNK%" (
    del "%STARTUP_LNK%"
    echo [SUCCESS] Auto-Run shortcut removed from Windows Startup.
) else (
    echo [INFO] Auto-Run shortcut was not installed in Windows Startup.
)
echo.
pause
