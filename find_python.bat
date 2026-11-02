@echo off
set "PYTHON_EXE="

:: 1. Check standard per-user and system-wide Python 3 installations
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist "%%~P" (
        "%%~P" -c "import sys" >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON_EXE=%%~P"
            goto :found
        )
    )
)

:: 2. Check 'python' in PATH (ignoring Windows Store stub in WindowsApps)
python -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto :found
)

:: 3. If --install flag was passed, install Python 3.12 via winget
if /i "%~1"=="--install" (
    echo [INFO] Real Python not found ^(only Windows Store stub or missing^).
    echo [INFO] Installing Python 3.12 via winget...
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        goto :found
    )
    if exist "%ProgramFiles%\Python312\python.exe" (
        set "PYTHON_EXE=%ProgramFiles%\Python312\python.exe"
        goto :found
    )
)

echo.
echo [ERROR] Real Python installation was not found!
if /i "%~1"=="--install" (
    echo Please install Python 3.12 manually from https://www.python.org/downloads/
    echo ^(Make sure to check "Add python.exe to PATH" during installation^).
) else (
    echo Please run install_requirements.bat first.
)
pause
exit /b 1

:found
exit /b 0

