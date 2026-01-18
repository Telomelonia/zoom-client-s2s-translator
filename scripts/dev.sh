#!/bin/bash
# Development script to start both Electron and Python backend

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Starting Zoom S2S Translator Development Environment"
echo "=================================================="

# Check Node.js version
echo "📦 Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js >= 20.0.0"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "❌ Node.js version must be >= 20.0.0 (found: $(node -v))"
    exit 1
fi
echo "✅ Node.js $(node -v)"

# Check Python version
echo "📦 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python >= 3.10"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ Python version must be >= 3.10 (found: $PYTHON_VERSION)"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"

# Install Electron dependencies
echo ""
echo "📦 Installing Electron dependencies..."
cd "$PROJECT_ROOT/electron"
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "✅ Node modules already installed"
fi

# Set up Python virtual environment
echo ""
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_ROOT/python"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Python dependencies installed"

# Check for .env file
echo ""
echo "🔑 Checking for environment variables..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  No .env file found. Copy .env.example to .env and configure:"
    echo "   cp .env.example .env"
    echo ""
fi

# Start development servers
echo ""
echo "🎯 Starting development servers..."
echo "=================================================="
echo ""
echo "Starting Python backend on stdio..."
echo "Starting Electron app with Vite dev server..."
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Trap to kill all background processes on exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Start Python backend in background
cd "$PROJECT_ROOT/python"
python3 src/main.py &
PYTHON_PID=$!

# Start Electron app (this will block)
cd "$PROJECT_ROOT/electron"
npm run dev

# Wait for both processes
wait $PYTHON_PID
