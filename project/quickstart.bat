@echo off
REM Quick start script for Smart Waste Management Environment (Windows)

echo Smart Waste Management Environment - Quick Start
echo ==================================================

REM Check Python version
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip > nul
pip install -r requirements.txt > nul
echo ^> Dependencies installed

REM Copy .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo ^! Edit .env file with your OpenAI API key
)

echo.
echo Ready to start!
echo.
echo Options:
echo 1. Run inference:    python inference.py
echo 2. Start API server: python -m uvicorn app:app --reload
echo.
pause
