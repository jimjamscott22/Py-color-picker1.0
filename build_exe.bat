@echo off
setlocal

rem Navigate to the folder containing this script
cd /d "%~dp0"

rem Check if uv is available
where uv >nul 2>&1
if errorlevel 1 (
    echo Error: uv is not installed. Install it from https://docs.astral.sh/uv/
    exit /b 1
)

set APP_NAME=ColorPicker

echo.
echo Building %%APP_NAME%%.exe without console window...
uv run --group build pyinstaller ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name "%APP_NAME%" ^
    color_picker.py

echo.
echo Done! Look in the dist folder for %APP_NAME%.exe
echo (dist\%APP_NAME%.exe)

endlocal


