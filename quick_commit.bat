@echo off
title CrewAI Quick Commit
cd /d "%~dp0"
echo ========================================
echo       CrewAI - Quick Git Commit
echo ========================================
echo.
git status -s
echo.
set /p desc="Enter your commit message: "
if "%desc%"=="" set desc="Update changes"

git add .
git commit -m "%desc%"

echo.
echo ========================================
echo [SUCCESS] Changes have been committed!
echo ========================================
timeout /t 3 >nul
