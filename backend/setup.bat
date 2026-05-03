@echo off
REM Setup script for Windows - Gym Management System Backend

echo.
echo ============================================
echo  Gym Management System - Backend Setup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error creating virtual environment
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    exit /b 1
)

echo [4/5] Copying .env template...
if not exist .env (
    copy .env.example .env
    echo Created .env file - please update with your database credentials
)

echo [5/5] Creating database tables...
python -c "from database import init_db; init_db(); print('Database initialized')"

echo.
echo ============================================
echo  Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Update .env with your PostgreSQL credentials
echo   2. Run: python seed_data.py (to populate demo data)
echo   3. Run: uvicorn main:app --reload
echo.
echo Backend will be available at: http://localhost:8000
echo API Docs at: http://localhost:8000/docs
echo.
