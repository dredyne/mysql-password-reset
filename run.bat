@echo off
REM MySQL Password Reset Tool - Windows Batch Script
REM This script runs the MySQL password reset tool with administrator privileges

setlocal enabledelayedexpansion

REM Get the script directory
set SCRIPT_DIR=%~dp0

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6 or higher from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if running as administrator
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: This script requires Administrator privileges
    echo Please run this script as Administrator
    pause
    exit /b 1
)

REM Run the MySQL reset script
echo Running MySQL Password Reset Tool...
echo.
python "%SCRIPT_DIR%src\main.py"

REM Capture exit code
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% equ 0 (
    echo.
    echo SUCCESS: Password reset completed
) else (
    echo.
    echo FAILED: Password reset did not complete successfully
)

pause
exit /b %EXIT_CODE%
