#!/bin/bash

# Navigate to the folder containing this script
cd "$(dirname "$0")"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Install it from https://docs.astral.sh/uv/"
    exit 1
fi

APP_NAME="ColorPicker"

echo ""
echo "Building ${APP_NAME} executable without console window..."
uv run --group build pyinstaller \
    --noconfirm \
    --onefile \
    --noconsole \
    --name "${APP_NAME}" \
    color_picker.py

echo ""
echo "Done! Look in the dist folder for ${APP_NAME}"
echo "(dist/${APP_NAME})"
