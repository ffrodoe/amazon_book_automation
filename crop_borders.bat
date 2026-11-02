@echo off
setlocal
cd /d "%~dp0"

call "%~dp0find_python.bat"
if errorlevel 1 exit /b 1

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
