@echo off
echo ========================================
echo Starting Celebium API Server
echo ========================================
echo.

if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Activate venv and run
call venv\Scripts\activate.bat
python -m app.main
