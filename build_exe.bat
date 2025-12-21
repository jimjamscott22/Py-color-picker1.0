@echo off
setlocal

rem Navigate to the folder containing this script
cd /d "%~dp0"

rem Install PyInstaller if it is not already available
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    py -m pip install --user --upgrade pyinstaller
)

set APP_NAME=ColorPicker

echo.
echo Building %%APP_NAME%%.exe without console window...
pyinstaller ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name "%APP_NAME%" ^
    color_picker.py

echo.
echo Done! Look in the dist folder for %APP_NAME%.exe
echo (dist\%APP_NAME%.exe)

endlocal


