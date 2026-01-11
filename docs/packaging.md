# Packaging a Castella App

This guide covers packaging Castella applications for distribution.

## Desktop Applications

### PyInstaller

[PyInstaller](https://pyinstaller.org/) packages your app as a standalone executable:

```bash
# With uv (recommended)
uv add --dev pyinstaller
uv run pyinstaller --onefile --windowed your_app.py

# With pip
pip install pyinstaller
pyinstaller --onefile --windowed your_app.py
```

**Options:**

- `--onefile`: Create a single executable file
- `--windowed`: Hide the console window (for GUI apps)
- `--name`: Set the output executable name

**Example with custom options:**

```bash
pyinstaller --onefile --windowed --name "MyApp" \
    --icon=icon.ico your_app.py
```

### Nuitka

[Nuitka](https://nuitka.net/) compiles Python to native code for better performance:

```bash
# With uv (recommended)
uv add --dev nuitka
uv run nuitka --standalone --onefile your_app.py

# With pip
pip install nuitka
nuitka --standalone --onefile your_app.py
```

**For GUI applications:**

```bash
# With uv
uv run nuitka --standalone --onefile --disable-console your_app.py

# With pip
nuitka --standalone --onefile --disable-console your_app.py
```

## Platform-Specific Notes

### Windows

- Include SDL2/GLFW DLLs if using those backends
- Set `PYSDL2_DLL_PATH` environment variable if needed
- Consider code signing for distribution

**SDL2 DLL handling:**

```python
import os
os.environ["PYSDL2_DLL_PATH"] = "path/to/sdl2/dlls"
```

### macOS

For proper macOS app bundles:

```bash
# Using PyInstaller
pyinstaller --onefile --windowed \
    --osx-bundle-identifier com.yourname.yourapp \
    your_app.py
```

**Notes:**

- Sign your app for distribution
- Create a proper `.app` bundle
- Test on different macOS versions

### Linux

**AppImage (recommended for distribution):**

1. Build with PyInstaller
2. Package as AppImage for portable distribution

**System packages:**

Ensure system libraries are available:

```bash
# Debian/Ubuntu
sudo apt install libgl1-mesa-glx libglfw3

# Fedora
sudo dnf install mesa-libGL glfw
```

## iOS Applications

Castella iOS apps are packaged using [BeeWare Briefcase](https://briefcase.readthedocs.io/).

### Prerequisites

- macOS with Xcode
- Rust toolchain with iOS targets
- Briefcase: `pip install briefcase`

### Quick Start

Use the unified build script:

```bash
# Build and run on iOS Simulator
./tools/build_ios.sh examples/ios_test_app

# With auto-download of dependencies
AUTO_DOWNLOAD_DEPS=1 ./tools/build_ios.sh examples/ios_test_app
```

### Manual Process

```bash
cd your_ios_app

# Create iOS project
uvx briefcase create iOS

# Build
uvx briefcase build iOS

# Run on Simulator
uvx briefcase run iOS
```

### Project Structure

```
your_ios_app/
├── pyproject.toml          # Briefcase configuration
├── src/
│   └── your_app/
│       ├── __init__.py     # Entry point
│       ├── __main__.py     # Required for iOS
│       └── app.py          # Your Castella app
└── build_ios.sh            # Optional convenience script
```

### Dependencies

iOS requires pre-built native libraries. Download them:

```bash
# Auto-download during build
AUTO_DOWNLOAD_DEPS=1 ./tools/build_ios.sh your_app

# Or download manually
./tools/download_ios_deps.sh
```

### App Store Submission

!!! warning "Not Yet Tested"
    App Store submission has not been tested. Physical device deployment requires an Apple Developer account for code signing.

For more details, see [iOS Documentation](ios.md).

## Web Deployment

For PyScript/Pyodide web applications, see [Getting Started - Web Browsers](getting-started.md#for-web-browsers).

### Basic Web Deployment

1. Create your HTML file with PyScript setup
2. Include your Python source
3. Deploy to any static file server

**Example project structure:**

```
my-web-app/
├── index.html
├── main.py
└── castella-0.2.3-py3-none-any.whl
```

### Hosting Options

- GitHub Pages (free)
- Netlify (free tier)
- Any static file hosting

## Handling Dependencies

### Data Files

Include data files (images, fonts, etc.):

**PyInstaller:**

```bash
pyinstaller --add-data "assets:assets" your_app.py
```

**In your code:**

```python
import sys
import os

if getattr(sys, 'frozen', False):
    # Running as compiled
    base_path = sys._MEIPASS
else:
    # Running as script
    base_path = os.path.dirname(__file__)

asset_path = os.path.join(base_path, 'assets', 'image.png')
```

### Hidden Imports

If PyInstaller misses some imports:

```bash
pyinstaller --hidden-import=castella.glfw_frame \
    --hidden-import=skia your_app.py
```

## Best Practices

1. **Test the packaged app** on a clean system without Python installed

2. **Include all backends** you might use, or specify the exact one

3. **Document system requirements** for your users

4. **Version your releases** with clear changelogs

5. **Consider installer tools** like NSIS (Windows) or create-dmg (macOS) for professional distribution
