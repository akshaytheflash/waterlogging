@echo off
REM Quick Start Script for Historical Waterlogging Prediction System
REM This script automates the setup process

echo ========================================
echo Historical Prediction System Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo [1/5] Installing Python dependencies...
pip install -r ml_requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo.

echo [2/5] Running database migration...
python scripts\migrate_historical_schema.py
if %errorlevel% neq 0 (
    echo ERROR: Database migration failed
    echo Please check your DATABASE_URL in .env file
    pause
    exit /b 1
)
echo.

echo [3/5] Downloading historical data...
python scripts\download_comprehensive_data.py
if %errorlevel% neq 0 (
    echo WARNING: Some data downloads may have failed
    echo Check data\historical\MANUAL_DOWNLOAD_INSTRUCTIONS.txt
)
echo.

echo [4/5] Training ML model...
echo This may take 10-30 minutes depending on your hardware...
python scripts\train_advanced_model.py
if %errorlevel% neq 0 (
    echo ERROR: Model training failed
    pause
    exit /b 1
)
echo.

echo [5/5] Generating predictions for today...
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (
    set TODAY=%%c-%%a-%%b
)
python scripts\predict_for_date.py %TODAY%
if %errorlevel% neq 0 (
    echo WARNING: Prediction generation failed
    echo You can run it manually later
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Start the server: npm start
echo 2. Open browser: http://localhost:3000/predictions.html
echo 3. Select a date and view predictions
echo.
echo For more information, see HISTORICAL_PREDICTION_SETUP.md
echo.
pause
