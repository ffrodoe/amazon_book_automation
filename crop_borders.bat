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

echo ========================================================
echo  KDP Coloring Book - Frame and Border Remover
echo ========================================================

set "INPUT_DIR=%~1"

if "%INPUT_DIR%"=="" (
    set /p "INPUT_DIR=Enter folder path containing images: "
)

if "%INPUT_DIR%"=="" (
    echo [ERROR] No folder path specified!
    pause
    exit /b 1
)

echo Processing folder: %INPUT_DIR%
echo.

"%PYTHON_EXE%" crop_borders.py -i "%INPUT_DIR%"

echo.
pause
