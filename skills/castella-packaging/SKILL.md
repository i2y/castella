---
name: castella-packaging
description: Package Castella applications for distribution using ux, PyInstaller, or Nuitka. Create executables, macOS app bundles, and cross-compile for other platforms.
---

# Castella App Packaging

**When to use**: "package Castella app", "create executable", "bundle for distribution", "macOS app bundle", "code signing", "cross-compile"

## ux (Recommended)

[ux](https://github.com/i2y/ux) creates single executables using uv. End users don't need Python installed.

### Installation

```bash
uv tool install ux-py
```

### Basic Usage

```bash
ux bundle --project . --output ./dist/
```

### Configuration (pyproject.toml)

```toml
[tool.ux]
entry = "your_app"
include = ["assets/"]

[tool.ux.macos]
icon = "assets/icon.png"
bundle_identifier = "com.example.yourapp"
bundle_name = "Your App"
```

### macOS App Bundle

```bash
# Signed .app bundle
ux bundle --format app --codesign --output ./dist/

# With DMG
ux bundle --format app --codesign --dmg --output ./dist/

# With notarization
ux bundle --format app --codesign --notarize --dmg --output ./dist/
```

### Cross-Compilation

```bash
ux bundle --target linux-x86_64 --output ./dist/
ux bundle --target windows-x86_64 --output ./dist/
```

### Supported Targets

| Target | PyPI |
|--------|------|
| darwin-x86_64 | Yes |
| darwin-aarch64 | Yes |
| linux-x86_64 | Yes |
| linux-aarch64 | GitHub |
| windows-x86_64 | Yes |

## PyInstaller

Alternative bundler:

```bash
uv add --dev pyinstaller
uv run pyinstaller --onefile --windowed your_app.py
```

## Nuitka

Compiles Python to native code:

```bash
uv add --dev nuitka
uv run nuitka --standalone --onefile --disable-console your_app.py
```

## Reference

- `docs/packaging.md` - Full packaging documentation
