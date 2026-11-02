@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  Installing Book Creation Automation Dependencies
echo ====================================================

call "%~dp0find_python.bat" --install
if errorlevel 1 exit /b 1

echo Using Python at: "%PYTHON_EXE%"
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install msvc-runtime
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 echo [ERROR] Failed to install dependencies from requirements.txt! & pause & exit /b 1

echo.
echo ====================================================
echo  Installation completed successfully!
echo ====================================================
pause
