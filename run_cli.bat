@echo off
setlocal
cd /d "%~dp0"

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

set "TARGET_DIR=%~1"
if "%TARGET_DIR%"=="" (
    set /p "TARGET_DIR=Enter folder path containing images: "
)
if "%TARGET_DIR%"=="" (
    echo [ERROR] No folder path specified!
    pause
    exit /b 1
)

echo Starting Book Creation CLI for: "%TARGET_DIR%"
"%PYTHON_EXE%" -m src.cli -i "%TARGET_DIR%" -f a4

echo.
pause
