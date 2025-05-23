#!/bin/bash
# Simple startup script for local development

# Display welcome banner
echo "=========================================================="
echo "  Crypto Trading Platform - Local Development Environment"
echo "=========================================================="
echo ""

# Check for requirements
echo "Checking requirements..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    echo "   Please install Python 3 and try again."
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not found."
    echo "   Please install Node.js and try again."
    exit 1
fi

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not found."
    echo "   Please install npm and try again."
    exit 1
fi

echo "✅ All requirements satisfied!"
echo ""

# Navigate to web_dashboard directory
cd "$(dirname "$0")/web_dashboard"

# Run the development script
echo "Starting local development servers..."
echo "Press Ctrl+C to stop both servers."
echo ""

./dev.sh

echo ""
echo "Servers stopped."
