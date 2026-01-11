#!/bin/bash
# iOS App Build Script for Castella
#
# Usage:
#   ./tools/build_ios.sh <app_directory>
#
# Examples:
#   ./tools/build_ios.sh examples/ios_test_app
#   ./tools/build_ios.sh examples/ios_charts_demo
#
# Environment Variables:
#   CASTELLA_IOS_DEPS    - Path to iOS dependencies (default: ~/castella-ios-deps)
#   SIMULATOR_DEVICE     - iOS Simulator device name (default: iPhone 17 Pro)
#   AUTO_DOWNLOAD_DEPS   - Set to "1" to auto-download dependencies if missing

set -e

# Validate arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <app_directory>"
    echo ""
    echo "Examples:"
    echo "  $0 examples/ios_test_app"
    echo "  $0 examples/ios_charts_demo"
    exit 1
fi

APP_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CASTELLA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve app directory (support both relative and absolute paths)
if [[ "$APP_DIR" = /* ]]; then
    APP_DIR_ABS="$APP_DIR"
else
    APP_DIR_ABS="$(cd "$CASTELLA_ROOT/$APP_DIR" 2>/dev/null && pwd)" || {
        echo "ERROR: App directory not found: $APP_DIR"
        exit 1
    }
fi

# Check for pyproject.toml to get app metadata
if [ ! -f "$APP_DIR_ABS/pyproject.toml" ]; then
    echo "ERROR: pyproject.toml not found in $APP_DIR_ABS"
    exit 1
fi

# Extract app name from pyproject.toml
APP_NAME=$(grep -E "^name *= *" "$APP_DIR_ABS/pyproject.toml" | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/' | tr '-' '_')
if [ -z "$APP_NAME" ]; then
    echo "ERROR: Could not extract app name from pyproject.toml"
    exit 1
fi

# Extract formal name for Xcode project
FORMAL_NAME=$(grep -E "^formal_name *= *" "$APP_DIR_ABS/pyproject.toml" | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
if [ -z "$FORMAL_NAME" ]; then
    # Fallback: convert app_name to title case
    FORMAL_NAME=$(echo "$APP_NAME" | tr '_' ' ' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')
fi

# Extract bundle prefix from pyproject.toml
BUNDLE_PREFIX=$(grep -E "^bundle *= *" "$APP_DIR_ABS/pyproject.toml" | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
if [ -z "$BUNDLE_PREFIX" ]; then
    echo "ERROR: Could not extract bundle identifier from pyproject.toml"
    exit 1
fi

# Construct full bundle ID (Briefcase format: bundle.app-name)
APP_NAME_DASHED=$(echo "$APP_NAME" | tr '_' '-')
BUNDLE_ID="${BUNDLE_PREFIX}.${APP_NAME_DASHED}"

SIMULATOR_DEVICE="${SIMULATOR_DEVICE:-iPhone 17 Pro}"

# iOS dependencies paths
IOS_DEPS_DIR="${CASTELLA_IOS_DEPS:-$HOME/castella-ios-deps}"
IOS_TARGET="ios-sim-arm64"

# Paths for dependencies (check multiple locations)
if [ -d "$IOS_DEPS_DIR/$IOS_TARGET/pydantic_core" ]; then
    PYDANTIC_CORE_IOS="$IOS_DEPS_DIR/$IOS_TARGET/pydantic_core"
    CASTELLA_SKIA_DYLIB="$IOS_DEPS_DIR/$IOS_TARGET/castella_skia.abi3.so"
elif [ -d "$CASTELLA_ROOT/pydantic-core-ios-build/$IOS_TARGET/pydantic_core" ]; then
    # Local build path (from tools/build_pydantic_core_ios.sh)
    PYDANTIC_CORE_IOS="$CASTELLA_ROOT/pydantic-core-ios-build/$IOS_TARGET/pydantic_core"
    CASTELLA_SKIA_DYLIB="$CASTELLA_ROOT/target/aarch64-apple-ios-sim/release/libcastella_skia.dylib"
else
    PYDANTIC_CORE_IOS=""
    CASTELLA_SKIA_DYLIB=""
fi

# Briefcase paths - convert formal name to directory name (remove spaces)
XCODE_APP_NAME=$(echo "$FORMAL_NAME" | tr -d ' ')
BUILD_DIR="$APP_DIR_ABS/build/$APP_NAME/ios/xcode"
APP_PACKAGES_SIM="$BUILD_DIR/$XCODE_APP_NAME/app_packages.iphonesimulator"
VENV_SITE="$CASTELLA_ROOT/.venv/lib/python3.12/site-packages"

echo "=== Castella iOS Build Script ==="
echo "App directory: $APP_DIR_ABS"
echo "App name: $APP_NAME"
echo "Formal name: $FORMAL_NAME"
echo "Bundle ID: $BUNDLE_ID"
echo "Simulator device: $SIMULATOR_DEVICE"
echo ""

# Check/download dependencies
# Need both pydantic-core AND castella-skia to be present
NEED_DOWNLOAD=0
if [ -z "$PYDANTIC_CORE_IOS" ] || [ ! -d "$PYDANTIC_CORE_IOS" ]; then
    NEED_DOWNLOAD=1
fi
if [ -z "$CASTELLA_SKIA_DYLIB" ] || [ ! -f "$CASTELLA_SKIA_DYLIB" ]; then
    NEED_DOWNLOAD=1
fi

if [ "$NEED_DOWNLOAD" = "1" ]; then
    if [ "${AUTO_DOWNLOAD_DEPS:-0}" = "1" ]; then
        echo "Dependencies not found or incomplete. Auto-downloading..."
        "$CASTELLA_ROOT/tools/download_ios_deps.sh" latest "$IOS_TARGET"
        PYDANTIC_CORE_IOS="$IOS_DEPS_DIR/$IOS_TARGET/pydantic_core"
        CASTELLA_SKIA_DYLIB="$IOS_DEPS_DIR/$IOS_TARGET/castella_skia.abi3.so"
    else
        echo "ERROR: iOS dependencies not found or incomplete!"
        echo ""
        echo "Option 1: Download pre-built dependencies"
        echo "  ./tools/download_ios_deps.sh"
        echo ""
        echo "Option 2: Auto-download on build"
        echo "  AUTO_DOWNLOAD_DEPS=1 ./tools/build_ios.sh <app_directory>"
        echo ""
        echo "Option 3: Build locally (advanced)"
        echo "  See https://i2y.github.io/castella/ios/ for build instructions"
        exit 1
    fi
fi

if [ ! -f "$CASTELLA_SKIA_DYLIB" ]; then
    echo "ERROR: castella-skia iOS dylib not found at $CASTELLA_SKIA_DYLIB"
    echo "The download may have failed or the release doesn't contain iOS dependencies."
    exit 1
fi

echo "Using pydantic-core from: $PYDANTIC_CORE_IOS"
echo "Using castella-skia from: $CASTELLA_SKIA_DYLIB"
echo ""

# Step 1: Create project with briefcase
echo "[1/6] Creating project with briefcase..."
cd "$APP_DIR_ABS"
rm -rf build
uvx briefcase create iOS

# Step 2: Copy dependencies to app_packages
echo "[2/6] Copying dependencies to app_packages..."

cp -r "$PYDANTIC_CORE_IOS" "$APP_PACKAGES_SIM/"
cp -r "$VENV_SITE/pydantic" "$APP_PACKAGES_SIM/"
cp -r "$VENV_SITE/annotated_types" "$APP_PACKAGES_SIM/"
cp "$VENV_SITE/typing_extensions.py" "$APP_PACKAGES_SIM/"
cp -r "$VENV_SITE/typing_inspection" "$APP_PACKAGES_SIM/"
cp -r "$CASTELLA_ROOT/castella" "$APP_PACKAGES_SIM/"
cp "$CASTELLA_SKIA_DYLIB" "$APP_PACKAGES_SIM/castella_skia.abi3.so"

echo "Packages copied:"
ls "$APP_PACKAGES_SIM/"

# Step 3: Build with Xcode
echo "[3/6] Building with Xcode..."
cd "$BUILD_DIR"
xcodebuild -project "$FORMAL_NAME.xcodeproj" \
    -scheme "$FORMAL_NAME" \
    -sdk iphonesimulator \
    -configuration Debug \
    build 2>&1 | tail -5

# Step 4: Find and copy packages to built app
echo "[4/6] Copying packages to built app..."
BUILT_APP=$(find ~/Library/Developer/Xcode/DerivedData -name "$FORMAL_NAME.app" -path "*/Debug-iphonesimulator/*" -type d 2>/dev/null | head -1)
if [ -z "$BUILT_APP" ]; then
    echo "ERROR: Built app not found in DerivedData"
    exit 1
fi
echo "Found built app at: $BUILT_APP"
BUILT_APP_PACKAGES="$BUILT_APP/app_packages"
cp -r "$PYDANTIC_CORE_IOS" "$BUILT_APP_PACKAGES/"
cp -r "$VENV_SITE/pydantic" "$BUILT_APP_PACKAGES/"
cp -r "$VENV_SITE/annotated_types" "$BUILT_APP_PACKAGES/"
cp "$VENV_SITE/typing_extensions.py" "$BUILT_APP_PACKAGES/"
cp -r "$VENV_SITE/typing_inspection" "$BUILT_APP_PACKAGES/"
cp -r "$CASTELLA_ROOT/castella" "$BUILT_APP_PACKAGES/"
cp "$CASTELLA_SKIA_DYLIB" "$BUILT_APP_PACKAGES/castella_skia.abi3.so"

# Step 5: Install on simulator
echo "[5/6] Installing on simulator..."
xcrun simctl install "$SIMULATOR_DEVICE" "$BUILT_APP"

echo ""
echo "=== Build complete! ==="
echo ""

# Step 6: Launch the app
echo "[6/6] Launching app with console output..."
xcrun simctl launch --console "$SIMULATOR_DEVICE" "$BUNDLE_ID"
