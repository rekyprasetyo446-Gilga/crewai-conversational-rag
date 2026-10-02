$StartupFolder = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Startup)
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = "C:\Users\rekyp\OneDrive\Desktop\crewai_conversational_rag" }

$ShortcutPath = Join-Path $StartupFolder "CrewAI RAG AutoRun.lnk"
$TargetVBS = Join-Path $ProjectRoot "launch_silent.vbs"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$TargetVBS`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Auto-runs CrewAI Conversational RAG with Service Worker & Always-Active Server"
$Shortcut.Save()

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Auto-Run Installed to Windows Startup!" -ForegroundColor Green
Write-Host " Location: $ShortcutPath" -ForegroundColor Cyan
Write-Host " Server and UI will now auto-start when Windows boots." -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Green
