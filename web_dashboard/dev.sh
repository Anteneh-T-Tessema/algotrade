#!/bin/bash
# Development script to run both frontend and backend locally

# Kill any processes on exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Set environment variables for development
export NODE_ENV=development
export REACT_APP_API_URL="http://localhost:8000/v1"

echo "🚀 Starting local development environment..."

# Check if Python virtualenv exists and activate it
if [ -d "../venv" ]; then
    echo "📦 Activating Python virtual environment..."
    source ../venv/bin/activate
else
    echo "⚠️ Python virtual environment not found at '../venv'."
    echo "Creating a new virtual environment..."
    python3 -m venv ../venv
    source ../venv/bin/activate
    pip install -r ../requirements.txt
fi

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start the backend server
echo "🔄 Starting backend server..."
python run_server.py &
BACKEND_PID=$!

# Give the backend a moment to start
sleep 3

# Start the frontend dev server
echo "🔄 Starting frontend development server..."
npm start &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
