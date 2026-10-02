@echo off
title Stop CrewAI Conversational RAG Server
cd /d "%~dp0"

echo ======================================================================
echo    Stopping CrewAI Conversational RAG Server (Port 8000)
echo ======================================================================
echo.

set FOUND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Terminating PID %%a listening on port 8000...
    taskkill /F /PID %%a >nul 2>&1
    set FOUND=1
)

if "%FOUND%"=="1" (
    echo.
    echo [SUCCESS] CrewAI Server stopped successfully.
) else (
    echo [INFO] No server was running on port 8000.
)

timeout /t 3
