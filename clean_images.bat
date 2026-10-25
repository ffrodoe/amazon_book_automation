@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  ChatGPT Image Background Cleaner (+40 Levels)
echo ====================================================

set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if not exist "%PYTHON_EXE%" (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo [ERROR] Python 3.12 was not found!
        pause
        exit /b 1
    )
)

set "TARGET_DIR=%~1"
if "%TARGET_DIR%"=="" set "TARGET_DIR=reference\FarmAdventures"

echo Target folder: "%TARGET_DIR%"
echo Whitening background to pure #FFFFFF...

"%PYTHON_EXE%" -c "import sys; from src.core.image_cleaner import ImageCleaner; out = ImageCleaner.clean_folder(sys.argv[1]); print(f'Successfully cleaned {len(out)} images into: {out[0] if out else \"\"}')" "%TARGET_DIR%"

echo.
echo Done!
pause
