#!/bin/bash

# Navigate to the folder containing this script
cd "$(dirname "$0")"

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    python3 -m pip install --user --upgrade pyinstaller
fi

APP_NAME="ColorPicker"

echo ""
echo "Building ${APP_NAME} executable without console window..."
pyinstaller \
    --noconfirm \
    --onefile \
    --noconsole \
    --name "${APP_NAME}" \
    color_picker.py

echo ""
echo "Done! Look in the dist folder for ${APP_NAME}"
echo "(dist/${APP_NAME})"
