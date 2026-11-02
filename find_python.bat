@echo off
set "PYTHON_EXE="

for %%P in ("%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" "%ProgramFiles%\Python314\python.exe" "%ProgramFiles%\Python313\python.exe" "%ProgramFiles%\Python312\python.exe" "%ProgramFiles%\Python311\python.exe" "%ProgramFiles%\Python310\python.exe") do if not defined PYTHON_EXE if exist "%%~P" set "PYTHON_EXE=%%~P"

if not defined PYTHON_EXE for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if /i "%%~xI"==".exe" if exist "%%~I" set "PYTHON_EXE=%%~I"

if not defined PYTHON_EXE for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)" 2^>nul') do if /i "%%~xI"==".exe" if exist "%%~I" set "PYTHON_EXE=%%~I"

if not defined PYTHON_EXE if /i "%~1"=="--install" echo [INFO] Installing Python 3.12 via winget... & winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements

if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE if exist "%ProgramFiles%\Python312\python.exe" set "PYTHON_EXE=%ProgramFiles%\Python312\python.exe"

if not defined PYTHON_EXE echo [ERROR] Python not found! Please run install_requirements.bat first. & pause & exit /b 1
exit /b 0
