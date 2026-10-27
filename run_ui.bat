@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  Launching KDP Coloring Book Studio (Web UI)
echo ====================================================

set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if not exist "%PYTHON_EXE%" (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo [ERROR] Python 3.12 was not found!
        echo Please run install_requirements.bat first.
        pause
        exit /b 1
    )
)

echo Starting server at http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000

"%PYTHON_EXE%" -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload
pause
