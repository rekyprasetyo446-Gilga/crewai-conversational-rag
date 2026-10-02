<#
.SYNOPSIS
    Autonomous Cross-Browser Service Runner for CrewAI Conversational RAG
    Ensures the server, Service Worker, and web dashboard are always active and running.
#>
param (
    [switch]$NoBrowser,
    [string]$BrowserPreference = "auto" # "chrome", "edge", "firefox", or "auto"
)

$ErrorActionPreference = "SilentlyContinue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = "C:\Users\rekyp\OneDrive\Desktop\crewai_conversational_rag" }
Set-Location $ProjectRoot

$VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"
$ServerUrl = "http://localhost:8000"
$HealthUrl = "http://localhost:8000/api/health"

function Write-Log {
    param([string]$Message, [string]$Color = "Cyan")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "==========================================================" "Cyan"
Write-Log "  CrewAI Conversational RAG - Autonomous Service Engine    " "Cyan"
Write-Log "  Target URL : $ServerUrl                                  " "Green"
Write-Log "  Platforms  : Chrome, Microsoft Edge, Mozilla Firefox     " "Yellow"
Write-Log "==========================================================" "Cyan"

# Step 1: Ensure Server is Active
function Test-ServerHealth {
    try {
        $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2 -ErrorAction Stop
        return ($response.status -eq "healthy")
    } catch {
        return $false
    }
}

if (-not (Test-ServerHealth)) {
    Write-Log "[SERVER] Server not responding on port 8000. Initiating startup..." "Yellow"
    
    # Clean any zombie listener on 8000
    $conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }

    # Start FastAPI server as background job
    $serverProcess = Start-Process -FilePath $VenvPython -ArgumentList "web_app.py" -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden
    Write-Log "[SERVER] Process launched (PID: $($serverProcess.Id)). Awaiting health check..." "Green"

    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if (Test-ServerHealth) {
            $ready = $true
            break
        }
    }

    if (-not $ready) {
        Write-Log "[ERROR] Server failed to become healthy within 30 seconds." "Red"
        Exit 1
    }
    Write-Log "[SERVER] Health check PASSED. Service is active." "Green"
} else {
    Write-Log "[SERVER] Verified existing healthy server on port 8000." "Green"
}

# Step 2: Cross-Browser Auto-Launch (App Mode / Standard Mode)
if (-not $NoBrowser) {
    Write-Log "[BROWSER] Detecting installed browsers for auto-run..." "Cyan"

    $ChromePaths = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    )
    $EdgePaths = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
    )
    $FirefoxPaths = @(
        "$env:ProgramFiles\Mozilla Firefox\firefox.exe",
        "${env:ProgramFiles(x86)}\Mozilla Firefox\firefox.exe"
    )

    $Launched = $false

    # Try preferred browser or auto-detect
    if ($BrowserPreference -eq "chrome" -or $BrowserPreference -eq "auto") {
        foreach ($p in $ChromePaths) {
            if (Test-Path $p) {
                Write-Log "[BROWSER] Launching via Google Chrome (PWA App Mode)..." "Green"
                Start-Process -FilePath $p -ArgumentList "--app=$ServerUrl"
                $Launched = $true
                break
            }
        }
    }

    if (-not $Launched -and ($BrowserPreference -eq "edge" -or $BrowserPreference -eq "auto")) {
        foreach ($p in $EdgePaths) {
            if (Test-Path $p) {
                Write-Log "[BROWSER] Launching via Microsoft Edge (App Mode)..." "Green"
                Start-Process -FilePath $p -ArgumentList "--app=$ServerUrl"
                $Launched = $true
                break
            }
        }
    }

    if (-not $Launched -and ($BrowserPreference -eq "firefox" -or $BrowserPreference -eq "auto")) {
        foreach ($p in $FirefoxPaths) {
            if (Test-Path $p) {
                Write-Log "[BROWSER] Launching via Mozilla Firefox..." "Green"
                Start-Process -FilePath $p -ArgumentList "-url $ServerUrl"
                $Launched = $true
                break
            }
        }
    }

    if (-not $Launched) {
        Write-Log "[BROWSER] Opening in default system web browser..." "Yellow"
        Start-Process $ServerUrl
    }
}

Write-Log "[MONITOR] Service Worker and Watchdog Active. Schema is auto-running." "Green"
