#!/bin/bash
# iOS All Widgets Demo Build Script
# This is a convenience wrapper for tools/build_ios.sh
#
# Environment Variables:
#   CASTELLA_IOS_DEPS    - Path to iOS dependencies (default: ~/castella-ios-deps)
#   SIMULATOR_DEVICE     - iOS Simulator device name (default: iPhone 17 Pro)
#   AUTO_DOWNLOAD_DEPS   - Set to "1" to auto-download dependencies if missing

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/../../tools/build_ios.sh" "$SCRIPT_DIR"
