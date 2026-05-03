@echo off
REM Setup script for Windows - Gym Management System Frontend

echo.
echo ============================================
echo  Gym Management System - Frontend Setup
echo ============================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    exit /b 1
)

echo Node.js version:
node --version

echo.
echo [1/3] Installing dependencies...
call npm install
if errorlevel 1 (
    echo Error installing dependencies
    exit /b 1
)

echo [2/3] Configuration complete.

echo [3/3] Build check...
call npm run build
if errorlevel 1 (
    echo Warning: Build had issues, but dev server can still run
)

echo.
echo ============================================
echo  Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Start backend: cd ..\backend && uvicorn main:app --reload
echo   2. Run: npm run dev
echo.
echo Frontend will be available at: http://localhost:5173
echo.
