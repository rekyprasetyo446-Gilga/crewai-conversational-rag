@echo off
title Install CrewAI Auto-Run on Windows Startup
cd /d "%~dp0"
echo Registering CrewAI RAG into Windows Startup...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_autorun.ps1"
echo.
pause
