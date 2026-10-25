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

echo Starting Book Creation CLI...
"%PYTHON_EXE%" -m src.cli -i "reference\FarmAdventures" -f a4

echo.
pause
