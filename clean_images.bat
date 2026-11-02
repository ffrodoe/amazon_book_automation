@echo off
setlocal
cd /d "%~dp0"

echo ====================================================
echo  ChatGPT Image Background Cleaner (+40 Levels)
echo ====================================================

call "%~dp0find_python.bat"
if errorlevel 1 exit /b 1

set "TARGET_DIR=%~1"
if "%TARGET_DIR%"=="" set /p "TARGET_DIR=Enter folder path containing images: "
if "%TARGET_DIR%"=="" echo [ERROR] No folder path specified! & pause & exit /b 1

echo Target folder: "%TARGET_DIR%"
echo Whitening background to pure #FFFFFF...

"%PYTHON_EXE%" -c "import sys; from src.core.image_cleaner import ImageCleaner; out = ImageCleaner.clean_folder(sys.argv[1]); print(f'Successfully cleaned {len(out)} images into: {out[0] if out else \"\"}')" "%TARGET_DIR%"

echo.
echo Done!
pause
