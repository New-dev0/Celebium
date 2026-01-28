@echo off
echo ========================================
echo Celebium Backend - Installation Script
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Python found
python --version

:: Create virtual environment
echo.
echo [2/4] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

:: Activate and install
echo.
echo [3/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

:: Test imports
echo.
echo [4/4] Testing installation...
python test_imports.py

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To run the server:
echo   1. Activate: venv\Scripts\activate
echo   2. Run: python -m app.main
echo.
echo Server will start on http://127.0.0.1:25325
echo API Docs: http://127.0.0.1:25325/docs
echo.
pause
