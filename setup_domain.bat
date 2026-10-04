@echo off
NET SESSION >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator privileges detected.
    echo Setting up crewairag.com in hosts file...
    
    findstr /C:"crewairag.com" "%WINDIR%\System32\drivers\etc\hosts" >nul
    if %errorlevel% neq 0 (
        echo 127.0.0.1 crewairag.com >> "%WINDIR%\System32\drivers\etc\hosts"
        echo Successfully added crewairag.com to hosts file.
    ) else (
        echo crewairag.com is already in the hosts file.
    )
    
    echo Running XAMPP Host Setup...
    .\.venv\Scripts\python.exe setup_xampp_host.py
    
    echo.
    echo Setup complete! You can now access http://crewairag.com
    pause
) else (
    echo Requesting Administrator privileges to update hosts file...
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
)
