# iOS Support

Castella runs on iOS with full widget support, including charts, data tables, and keyboard/IME input.

!!! note "Work in Progress"
    iOS support is functional on the Simulator. Physical device deployment and Android support are planned.

## Overview

- **Rendering**: castella-skia with Metal backend
- **Packaging**: BeeWare Briefcase
- **Python Runtime**: Python XCFramework via Briefcase
- **Targets**: iOS Simulator (arm64), iOS Device (arm64)

## Quick Start

```bash
# Build and run the all-widgets demo on iOS Simulator
./tools/build_ios.sh examples/ios_all_widgets_demo

# Or with auto-download of dependencies
AUTO_DOWNLOAD_DEPS=1 ./tools/build_ios.sh examples/ios_all_widgets_demo
```

## Demo Apps

Three demo apps showcase Castella's iOS capabilities:

| App | Location | Features |
|-----|----------|----------|
| Counter | `examples/ios_test_app/` | Basic Counter with increment/decrement buttons |
| Charts | `examples/ios_charts_demo/` | BarChart, LineChart, PieChart, GaugeChart |
| All Widgets | `examples/ios_all_widgets_demo/` | Full widget showcase with 6 tabs |

### All Widgets Demo

The most comprehensive demo includes:

- **Basic Tab**: Text, Button, Switch, Slider
- **Input Tab**: Input, MultilineInput with keyboard/IME
- **Layout Tab**: Column, Row, Box layouts
- **Data Tab**: DataTable, Tree
- **Media Tab**: NetImage, Modal
- **Charts Tab**: All chart types
- **Theme Toggle**: Dark/Light mode switching

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Castella App (Python via Rubicon-ObjC)             │
│  ├── PythonAppDelegate                              │
│  ├── UIWindow + UIViewController                    │
│  └── UIImageView for display                        │
├─────────────────────────────────────────────────────┤
│  castella-skia (Rust + PyO3)                        │
│  ├── Surface::from_metal(device, queue, w, h)       │
│  ├── SkiaPainter for drawing                        │
│  └── get_rgba_data() for pixel extraction           │
├─────────────────────────────────────────────────────┤
│  CoreGraphics (via ctypes)                          │
│  ├── CGDataProvider → CGImage → UIImage             │
│  └── Display in UIImageView                         │
└─────────────────────────────────────────────────────┘
```

### Key Components

- **iOSFrame** (`castella/ios_frame.py`): iOS-specific frame implementation
- **castella-skia**: Rust Skia bindings with Metal backend
- **Rubicon-ObjC**: Python-to-Objective-C bridge for UIKit access

### Touch Event Mapping

| iOS Event | Castella Event |
|-----------|----------------|
| `touchesBegan` | `MouseEvent` (mouse_down) |
| `touchesEnded` | `MouseEvent` (mouse_up) |
| `touchesMoved` | `MouseEvent` (mouse_drag) |
| Pinch gesture | `WheelEvent` |
| Soft keyboard | `InputCharEvent` / `InputKeyEvent` |

## Building iOS Apps

### Prerequisites

- macOS with Xcode installed
- Rust toolchain with iOS targets:
  ```bash
  rustup target add aarch64-apple-ios-sim  # M1/M2 Simulator
  rustup target add aarch64-apple-ios      # Physical device
  ```
- Briefcase: `pip install briefcase` or use `uvx briefcase`

### Using the Build Script

The unified build script handles all steps:

```bash
# Basic usage
./tools/build_ios.sh examples/ios_test_app

# With auto-download of pre-built dependencies
AUTO_DOWNLOAD_DEPS=1 ./tools/build_ios.sh examples/ios_test_app

# Each demo app also has a convenience wrapper
cd examples/ios_test_app
./build_ios.sh
```

### Manual Build Steps

```bash
cd examples/ios_test_app

# Create iOS project
uvx briefcase create iOS

# Build the app
uvx briefcase build iOS

# Run on Simulator
uvx briefcase run iOS
```

## Dependencies

iOS apps require pre-built native libraries (pydantic-core, castella-skia) that are cross-compiled for iOS.

### Auto-Download (Recommended)

Dependencies are automatically downloaded when using `AUTO_DOWNLOAD_DEPS=1`:

```bash
AUTO_DOWNLOAD_DEPS=1 ./tools/build_ios.sh examples/ios_test_app
```

### Manual Download

```bash
# Download iOS dependencies from GitHub Releases
./tools/download_ios_deps.sh [version] [target]

# Examples
./tools/download_ios_deps.sh              # Latest, ios-sim-arm64
./tools/download_ios_deps.sh latest ios-arm64   # Latest, device build
./tools/download_ios_deps.sh v0.11.0 ios-sim-arm64  # Specific version
```

### Build Locally

```bash
# Build pydantic-core for iOS
./tools/build_pydantic_core_ios.sh        # iOS Simulator (default)
./tools/build_pydantic_core_ios.sh device # iOS Device
./tools/build_pydantic_core_ios.sh all    # Both targets

# Build castella-skia for iOS
cd bindings/python && ./build_ios.sh

# Then build any iOS app
./tools/build_ios.sh examples/ios_test_app
```

### Dependency Locations

| Variable | Default | Description |
|----------|---------|-------------|
| `CASTELLA_IOS_DEPS` | `~/castella-ios-deps` | Base directory for iOS deps |

Downloaded files:
```
~/castella-ios-deps/
├── ios-sim-arm64/           # M1/M2 Mac Simulator
│   ├── pydantic_core/
│   └── castella_skia.abi3.so
└── ios-arm64/               # Physical device
    ├── pydantic_core/
    └── castella_skia.abi3.so
```

## Keyboard Input

iOS keyboard input is implemented with full IME (Input Method Editor) support for Japanese, Chinese, Korean, and other languages.

### Architecture

1. **Hidden UITextField**: Provides full IME support
2. **UITextFieldTextDidChangeNotification**: Monitors text changes
3. **Diff computation**: Calculates inserted/deleted characters

### Usage

- `Input` and `MultilineInput` widgets automatically show the keyboard when focused
- ASCII input uses direct character events
- IME input (e.g., Japanese) works via text field diff computation

### Supported Input Methods

- Direct ASCII input
- Japanese IME (Hiragana, Katakana, Kanji)
- Chinese IME (Pinyin, Zhuyin)
- Korean IME (Hangul)
- Any IME supported by iOS

## Safe Area Handling

iOS devices with notches (iPhone X and later) have safe area insets. Castella handles this automatically:

- Status bar area is respected
- Home indicator area is respected
- Content is rendered within safe bounds

## Limitations

- **Android**: Not yet supported (planned)
- **Physical devices**: Requires Apple Developer account for code signing
- **App Store**: Not yet tested for App Store submission

## Troubleshooting

### Build Failures

**Missing dependencies**:
```bash
# Ensure iOS dependencies are downloaded
./tools/download_ios_deps.sh
```

**Xcode command line tools**:
```bash
xcode-select --install
```

### Runtime Issues

**Black screen**: Ensure castella-skia is properly installed in app_packages

**Touch not working**: Check that `userInteractionEnabled = True` is set on UIImageView

**Keyboard not appearing**: Ensure the Input widget has focus

## Next Steps

- See [castella-skia](castella-skia.md) for details on the Rust rendering backend
- See [Packaging](packaging.md) for distribution options
