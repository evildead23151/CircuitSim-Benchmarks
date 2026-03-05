@echo off
echo ============================================
echo   CircuitSim Benchmarks - Local Startup
echo ============================================

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is required. Install from https://python.org
    exit /b 1
)

:: Check Node
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js is required. Install from https://nodejs.org
    exit /b 1
)

echo [1/5] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/5] Installing backend dependencies...
pip install -q -r backend\requirements.txt

echo [3/5] Generating training data and training model...
if not exist "sample_data\topological_v3_model.pkl" (
    echo   Generating dataset...
    python scripts\generate_topological_dataset_v3.py
    echo   Training model...
    python scripts\train_topological_v3.py
) else (
    echo   Model already exists, skipping training.
)

echo [4/5] Installing frontend dependencies...
cd frontend
call npm install --silent
cd ..

echo.
echo ============================================
echo   Setup Complete! Starting services...
echo ============================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.

:: Start backend
start "CircuitSim Backend" cmd /c "cd backend && ..\\.venv\\Scripts\\uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend
echo Waiting for backend...
timeout /t 5 /nobreak >nul

:: Start frontend
start "CircuitSim Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo CircuitSim Benchmarks is LIVE!
echo Close the terminal windows to stop services.
pause
