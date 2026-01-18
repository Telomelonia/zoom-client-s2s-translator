#!/bin/bash
# Script to install BlackHole virtual audio driver on macOS

set -e

echo "🔊 BlackHole Virtual Audio Driver Installer"
echo "==========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    echo "For Windows, please install VB-Audio Virtual Cable from:"
    echo "https://vb-audio.com/Cable/"
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed"
    echo "Please install Homebrew first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew is installed"
echo ""

# Check if BlackHole is already installed
if brew list --cask blackhole-2ch &> /dev/null; then
    echo "✅ BlackHole 2ch is already installed"
    echo ""
else
    echo "📦 Installing BlackHole 2ch..."
    brew install --cask blackhole-2ch
    echo "✅ BlackHole 2ch installed successfully"
    echo ""
fi

# Verify installation
echo "🔍 Verifying installation..."
if system_profiler SPAudioDataType | grep -q "BlackHole"; then
    echo "✅ BlackHole is available in system audio devices"
    echo ""
    echo "📝 Next steps:"
    echo "1. Open System Settings > Sound"
    echo "2. Verify 'BlackHole 2ch' appears in output devices"
    echo "3. In Zoom, set 'BlackHole 2ch' as your microphone"
    echo "4. The translator will route audio through this virtual device"
    echo ""
else
    echo "⚠️  BlackHole installed but not detected in audio devices"
    echo "You may need to restart your computer"
    echo ""
fi

echo "✅ Installation complete!"
