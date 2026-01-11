#!/bin/bash
# Build castella-skia for iOS Simulator (arm64)
#
# Prerequisites:
#   - Rust target: rustup target add aarch64-apple-ios-sim
#
# Usage:
#   cd bindings/python
#   ./build_ios.sh

set -ex

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR"

# Cross-compile for iOS Simulator (same as CI workflow)
PYO3_CROSS_PYTHON_VERSION="3.14" \
  cargo build --release --target aarch64-apple-ios-sim

CASTELLA_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo ""
echo "Build complete! Output at:"
echo "  $CASTELLA_ROOT/target/aarch64-apple-ios-sim/release/libcastella_skia.dylib"
