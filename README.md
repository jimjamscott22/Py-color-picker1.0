# 🎨 Py-color-picker1.0

A feature-rich color picker application built with Python and Tkinter, perfect for designers, developers, and anyone working with colors.

## ✨ Features

- **Visual Color Picker**: Interactive color selection with live preview
- **Multiple Color Formats**: Display colors in HEX, RGB, and HSL formats
- **HSV Sliders**: Fine-tune hue, saturation, and value with live updates
- **Contrast Checks**: WCAG contrast ratios against white, black, and a custom background
- **Color History**: Automatically tracks your last 10 colors
- **Favorites System**: Save and manage your favorite colors (persisted to disk)
- **Palette Swatches**: Clickable history/favorites swatches for fast reuse
- **Palette Import/Export**: Save and load palettes as JSON
- **Manual HEX Input**: Enter HEX codes directly with validation
- **Quick Copy**: One-click copy to clipboard for HEX, RGB, and HSL values
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- tkinter (usually included with Python)

On Linux, you may need to install tkinter:

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

### Running from Source

```bash
# Clone the repository
git clone <your-repo-url>
cd Py-color-picker1.0

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 color_picker.py
```

## 🔨 Building Executable

### Windows

```bash
build_exe.bat
```

### Linux/macOS

```bash
chmod +x build_exe.sh
./build_exe.sh
```

The executable will be created in the `dist/` folder.

## 🎯 Usage

1. **Pick a Color**: Click "Pick a Color" to open the color chooser dialog
2. **Manual Input**: Enter HEX codes directly (e.g., `#1A2B3C` or `ABC`)
3. **Copy Values**: Click "Copy HEX" or "Copy RGB" to copy to clipboard
4. **Save Favorites**: Click "Add to Favorites" to save the current color
5. **Reuse Colors**: Double-click any color in History or Favorites to reuse it
6. **Remove Favorites**: Select a favorite and click "Remove Selected"

## 💾 Data Storage

Favorite colors are automatically saved to `~/.color_picker_favorites.json` and loaded on startup.
Palette exports are saved as JSON files containing both favorites and recent history.

## 🛠️ Technologies

- Python 3
- Tkinter (GUI framework)
- ttkbootstrap (modern Tkinter theme)
- colorsys (color conversion)
- PyInstaller (for building executables)

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
