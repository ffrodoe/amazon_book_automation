@echo off
setlocal
cd /d "%~dp0"

call "%~dp0find_python.bat"
if errorlevel 1 exit /b 1

set "TARGET_DIR=%~1"
if "%TARGET_DIR%"=="" set /p "TARGET_DIR=Enter folder path containing images: "
if "%TARGET_DIR%"=="" echo [ERROR] No folder path specified! & pause & exit /b 1

echo Starting Book Creation CLI for: "%TARGET_DIR%"
"%PYTHON_EXE%" -m src.cli -i "%TARGET_DIR%" -f a4

echo.
pause
