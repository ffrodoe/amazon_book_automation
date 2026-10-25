@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  Installing Book Creation Automation Dependencies
echo ====================================================

set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if not exist "%PYTHON_EXE%" (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo [INFO] Python not found. Installing Python 3.12 via winget...
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    )
)

echo Using Python at: "%PYTHON_EXE%"
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo.
echo ====================================================
echo  Installation completed successfully!
echo ====================================================
pause
