@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  Launching KDP Coloring Book Studio (Web UI)
echo ====================================================

call "%~dp0find_python.bat"
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -c "import uvicorn" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Dependencies not installed yet. Installing from requirements.txt...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
)

echo Starting server at http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000

"%PYTHON_EXE%" -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload
pause
