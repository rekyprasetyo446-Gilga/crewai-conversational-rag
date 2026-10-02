@echo off
title CrewAI Conversational RAG Server (Persistent)
cd /d "%~dp0"

echo ======================================================================
echo    Starting CrewAI Conversational RAG Server & Web Dashboard
echo ======================================================================
echo.

:: Clean up any lingering port 8000 processes before starting
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo [CLEANUP] Freeing existing port 8000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

:: Launch health poller in background that opens browser only when port 8000 is ready
start /min "" powershell -NoProfile -ExecutionPolicy Bypass -Command "$port = 8000; Write-Host 'Waiting for server...'; for ($i = 0; $i -lt 120; $i++) { Start-Sleep -Seconds 1; $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; if ($conn) { Start-Sleep -Seconds 1; Start-Process 'http://localhost:8000'; break } }"

:server_loop
echo [STATUS] Launching CrewAI RAG Server on http://localhost:8000 ...
echo [INFO] The server will stay ALWAYS ACTIVE while you browse the site.
echo [INFO] Press Ctrl+C in this window when you wish to stop the server.
echo.

".venv\Scripts\python.exe" web_app.py

echo.
echo ======================================================================
echo [WARNING] Server stopped at %TIME%. 
echo Restarting server in 3 seconds to keep it always active...
echo (Press Ctrl+C to permanently close)
echo ======================================================================
timeout /t 3 >nul
goto server_loop
