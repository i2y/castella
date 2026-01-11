#!/bin/bash
# Download iOS dependencies for Castella
#
# Usage:
#   ./tools/download_ios_deps.sh [version] [target]
#
# Arguments:
#   version: Castella version (default: latest)
#   target:  ios-sim-arm64 or ios-arm64 (default: ios-sim-arm64)
#
# Example:
#   ./tools/download_ios_deps.sh v0.11.0 ios-sim-arm64

set -e

VERSION="${1:-latest}"
TARGET="${2:-ios-sim-arm64}"
REPO="i2y/castella"
DEST_DIR="${CASTELLA_IOS_DEPS:-$HOME/castella-ios-deps}"

echo "=== Castella iOS Dependencies Downloader ==="
echo "Version: $VERSION"
echo "Target: $TARGET"
echo "Destination: $DEST_DIR"
echo ""

# Get download URL
if [ "$VERSION" = "latest" ]; then
    RELEASE_URL="https://api.github.com/repos/$REPO/releases/latest"
else
    RELEASE_URL="https://api.github.com/repos/$REPO/releases/tags/$VERSION"
fi

echo "Fetching release info..."
DOWNLOAD_URL=$(curl -s "$RELEASE_URL" | grep "browser_download_url.*${TARGET}.tar.gz" | head -1 | cut -d '"' -f 4)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "ERROR: Could not find ${TARGET}.tar.gz in release $VERSION"
    echo ""
    echo "Available releases:"
    curl -s "https://api.github.com/repos/$REPO/releases" | grep '"tag_name"' | head -5 | cut -d '"' -f 4
    exit 1
fi

echo "Downloading from: $DOWNLOAD_URL"

# Create destination directory
mkdir -p "$DEST_DIR"

# Download and extract
TARBALL="$DEST_DIR/${TARGET}.tar.gz"
curl -L -o "$TARBALL" "$DOWNLOAD_URL"

echo "Extracting..."
tar xzf "$TARBALL" -C "$DEST_DIR"
rm "$TARBALL"

echo ""
echo "=== Download complete! ==="
echo ""
echo "Files extracted to: $DEST_DIR/$TARGET/"
echo ""
echo "Contents:"
ls -la "$DEST_DIR/$TARGET/"
echo ""
echo "To use with build_ios.sh:"
echo "  export CASTELLA_IOS_DEPS=$DEST_DIR"
echo "  cd examples/ios_test_app && ./build_ios.sh"
