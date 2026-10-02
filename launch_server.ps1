<#
.SYNOPSIS
    Persistent Launcher for CrewAI Conversational RAG Dashboard
#>
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$python = "$ProjectRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "[ERROR] Virtual environment not found at $python" -ForegroundColor Red
    Pause
    Exit 1
}

# Free port 8000 if occupied
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "[CLEANUP] Evicting process $($conn.OwningProcess) on port 8000..." -ForegroundColor Yellow
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Starting CrewAI Conversational RAG Server & UI        " -ForegroundColor Cyan
Write-Host "   Web UI : http://localhost:8000                        " -ForegroundColor Green
Write-Host "   Docs   : http://localhost:8000/docs                   " -ForegroundColor Green
Write-Host "   Mode   : Always Active (Auto-Recovery Enabled)        " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Background Poller: Wait for port 8000 to be ready, then open browser
Start-Job -ScriptBlock {
    for ($i = 0; $i -lt 120; $i++) {
        Start-Sleep -Seconds 1
        $c = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
        if ($c) {
            Start-Sleep -Seconds 1
            Start-Process "http://localhost:8000"
            break
        }
    }
} | Out-Null

while ($true) {
    Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Starting CrewAI Server..." -ForegroundColor Green
    & $python web_app.py
    Write-Host "[WARNING] Server exited at $(Get-Date -Format 'HH:mm:ss'). Restarting in 3 seconds (Ctrl+C to abort)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}
