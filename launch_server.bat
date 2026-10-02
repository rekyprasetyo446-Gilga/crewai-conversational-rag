@echo off
title CrewAI Conversational RAG Server (Persistent)
cd /d "%~dp0"

echo ======================================================================
echo    Starting CrewAI Conversational RAG Server & Web Dashboard
echo ======================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch_server.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server launcher encountered an error (%ERRORLEVEL%).
    pause
)
