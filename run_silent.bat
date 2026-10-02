@echo off
title CrewAI Conversational RAG - Silent Auto-Run
cd /d "%~dp0"

echo Starting CrewAI Conversational RAG silently in background...
wscript.exe "%~dp0launch_silent.vbs"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Server and UI launched in background.
) else (
    echo [ERROR] Launch failed with code %ERRORLEVEL%.
)
timeout /t 3 >nul
