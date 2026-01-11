#!/bin/bash
# Build pydantic-core for iOS
#
# Prerequisites:
#   - Rust targets: rustup target add aarch64-apple-ios-sim aarch64-apple-ios
#
# Usage:
#   ./tools/build_pydantic_core_ios.sh [target]
#
# Targets:
#   sim     - iOS Simulator (arm64) - default
#   device  - iOS Device (arm64)
#   all     - Both targets
#
# Output:
#   pydantic-core-ios-build/

set -e

TARGET="${1:-sim}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CASTELLA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$CASTELLA_ROOT/pydantic-core-ios-build"
PYDANTIC_CORE_DIR="$BUILD_DIR/pydantic-core"

echo "=== pydantic-core iOS Build Script ==="
echo "Target: $TARGET"
echo "Build directory: $BUILD_DIR"
echo ""

# Create build directory
mkdir -p "$BUILD_DIR"

# Clone or update pydantic-core
if [ -d "$PYDANTIC_CORE_DIR" ]; then
    echo "[1/4] Updating pydantic-core..."
    cd "$PYDANTIC_CORE_DIR"
    git fetch origin
    git reset --hard origin/main
else
    echo "[1/4] Cloning pydantic-core..."
    git clone https://github.com/pydantic/pydantic-core.git "$PYDANTIC_CORE_DIR"
    cd "$PYDANTIC_CORE_DIR"
fi

# Patch Cargo.toml to add extension-module feature
echo "[2/4] Patching Cargo.toml..."
if grep -q 'extension-module' Cargo.toml; then
    echo "  Already patched"
else
    # Add extension-module to the existing pyo3 features list
    # Original: pyo3 = { version = "0.23", features = ["generate-import-lib", ...] }
    # Patched:  pyo3 = { version = "0.23", features = ["extension-module", "generate-import-lib", ...] }
    sed -i '' 's/pyo3 = { version = "\([^"]*\)", features = \["/pyo3 = { version = "\1", features = ["extension-module", "/' Cargo.toml
    echo "  Patched pyo3 dependency"
fi

# Create .cargo/config.toml with linker flags
echo "[3/4] Creating .cargo/config.toml..."
mkdir -p .cargo
cat > .cargo/config.toml << 'EOF'
[target.aarch64-apple-ios]
rustflags = ["-C", "link-arg=-undefined", "-C", "link-arg=dynamic_lookup"]

[target.aarch64-apple-ios-sim]
rustflags = ["-C", "link-arg=-undefined", "-C", "link-arg=dynamic_lookup"]

[target.x86_64-apple-ios]
rustflags = ["-C", "link-arg=-undefined", "-C", "link-arg=dynamic_lookup"]
EOF

# Build for specified target(s)
echo "[4/4] Building..."

build_simulator() {
    echo "  Building for iOS Simulator (arm64)..."
    PYO3_CROSS_PYTHON_VERSION="3.14" \
        cargo build --release --target aarch64-apple-ios-sim -j 2
}

build_device() {
    echo "  Building for iOS Device (arm64)..."
    PYO3_CROSS_PYTHON_VERSION="3.14" \
        cargo build --release --target aarch64-apple-ios -j 2
}

case "$TARGET" in
    sim)
        build_simulator
        ;;
    device)
        build_device
        ;;
    all)
        build_simulator
        build_device
        ;;
    *)
        echo "ERROR: Unknown target '$TARGET'"
        echo "Valid targets: sim, device, all"
        exit 1
        ;;
esac

# Copy Python files to build output
echo ""
echo "=== Packaging output ==="

package_output() {
    local rust_target="$1"
    local output_name="$2"
    local output_dir="$BUILD_DIR/$output_name"

    mkdir -p "$output_dir/pydantic_core"

    # Copy dylib as .abi3.so
    cp "target/$rust_target/release/lib_pydantic_core.dylib" \
       "$output_dir/pydantic_core/_pydantic_core.abi3.so"

    # Copy Python files
    cp python/pydantic_core/*.py "$output_dir/pydantic_core/"

    echo "  $output_dir/pydantic_core/"
}

case "$TARGET" in
    sim)
        package_output "aarch64-apple-ios-sim" "ios-sim-arm64"
        ;;
    device)
        package_output "aarch64-apple-ios" "ios-arm64"
        ;;
    all)
        package_output "aarch64-apple-ios-sim" "ios-sim-arm64"
        package_output "aarch64-apple-ios" "ios-arm64"
        ;;
esac

echo ""
echo "=== Build complete! ==="
echo ""
echo "Output directories:"
case "$TARGET" in
    sim)
        echo "  $BUILD_DIR/ios-sim-arm64/pydantic_core/"
        ;;
    device)
        echo "  $BUILD_DIR/ios-arm64/pydantic_core/"
        ;;
    all)
        echo "  $BUILD_DIR/ios-sim-arm64/pydantic_core/"
        echo "  $BUILD_DIR/ios-arm64/pydantic_core/"
        ;;
esac
echo ""
echo "To use with tools/build_ios.sh, the script will auto-detect this location."
