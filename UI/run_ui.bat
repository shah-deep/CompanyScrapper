@echo off
echo 🏢 Company Crawler & Scrapper UI
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory structure
if not exist "UI\app.py" (
    echo ❌ UI\app.py not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Run the launcher script
python UI\run_ui.py

pause 