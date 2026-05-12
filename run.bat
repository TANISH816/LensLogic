@echo off
set BACKEND_DIR=lenslogic-backend
set FRONTEND_DIR=lenslogic-ui

echo === Step 1: Installing/Updating Dependencies ===
cd %BACKEND_DIR%
if exist requirements.txt (
    echo Installing Python packages...
    pip install -r requirements.txt
)
cd ..\%FRONTEND_DIR%
if exist package.json (
    echo Installing Node packages...
    call npm install
)

echo === Step 2: Starting Services ===
cd ..
:: Start Backend in a new background process
:: If using FastAPI:
start /b cmd /c "cd %BACKEND_DIR% && uvicorn main:app --reload --port 8000"
:: OR if using pure Django:
:: start /b cmd /c "cd %BACKEND_DIR% && python manage.py runserver 8000"

:: Start Frontend in the current window
cd %FRONTEND_DIR%
npm run dev
