@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  Launching KDP Coloring Book Studio (Web UI)
echo ====================================================

call "%~dp0find_python.bat"
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" "%~dp0launch_ui.py"
pause
