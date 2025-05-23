#!/bin/bash
#
# Master script to run the entire strategy analysis and dashboard system
# This script will:
# 1. Activate the Python environment (if needed)
# 2. Run the notebook to generate data files
# 3. Start the API server
# 4. Monitor and display logs
#
# Author: GitHub Copilot
# Date: May 20, 2025

# Enable error handling
set -e

# Configuration
PROJECT_ROOT="/Users/antenehtessema/Desktop/botsalgo"
LOG_DIR="${PROJECT_ROOT}/logs"
DATA_DIR="${PROJECT_ROOT}/data"
PORT=8000

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log file for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/system_run_${TIMESTAMP}.log"
API_LOG_FILE="${LOG_DIR}/api_server_${TIMESTAMP}.log"

# Function to log messages
log() {
    local message="$1"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "[$timestamp] $message" | tee -a "$LOG_FILE"
}

log "Starting the strategy analysis and dashboard system"
log "Project root: $PROJECT_ROOT"
log "Log file: $LOG_FILE"

# Change to the project directory
cd "$PROJECT_ROOT"
log "Changed to project directory: $(pwd)"

# Check if Python is available
if ! command -v python &> /dev/null; then
    log "ERROR: Python is not available. Please install Python."
    exit 1
fi

log "Using Python: $(which python)"
log "Python version: $(python --version)"

# Check if required packages are installed
log "Checking required Python packages..."
python -c "import pandas, numpy, jupyter, fastapi, uvicorn, plotly" 2>/dev/null || {
    log "Installing required packages..."
    pip install pandas numpy jupyter notebook nbconvert fastapi uvicorn plotly tabulate requests
}

# Step 1: Run the analysis notebook to generate the data files
log "Step 1: Running the analysis notebook to generate data files..."
jupyter nbconvert --to python --execute strategy_results_analysis.ipynb --output=tmp_analysis.py

# Verify that the data files were created
if [[ -f "${DATA_DIR}/summary_report.csv" && -f "${DATA_DIR}/weight_table.json" ]]; then
    log "Data files successfully generated:"
    log "  - ${DATA_DIR}/summary_report.csv ($(wc -l < ${DATA_DIR}/summary_report.csv) lines)"
    log "  - ${DATA_DIR}/weight_table.json ($(wc -l < ${DATA_DIR}/weight_table.json) lines)"
else
    log "ERROR: Data files were not generated correctly."
    [[ ! -f "${DATA_DIR}/summary_report.csv" ]] && log "Missing: ${DATA_DIR}/summary_report.csv"
    [[ ! -f "${DATA_DIR}/weight_table.json" ]] && log "Missing: ${DATA_DIR}/weight_table.json"
    exit 1
fi

# Step 2: Check the EnsembleStrategy implementation
log "Step 2: Testing the EnsembleStrategy implementation..."
python test_ensemble.py

# Step 3: Start the API server
log "Step 3: Starting the API server on port $PORT..."
log "API server logs will be written to: $API_LOG_FILE"

# Create a simplified API server script if it doesn't exist already
if [[ ! -f "runtime_api_server.py" ]]; then
    log "Creating a runtime API server script..."
    cat > runtime_api_server.py << 'EOF'
#!/usr/bin/env python3
"""
Simple API server for serving analysis data
"""
import os
import sys
import json
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Get the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Create the FastAPI app
app = FastAPI(
    title="Strategy Analysis API",
    description="API for strategy backtesting analysis and weights",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define routes
@app.get("/v1/analysis/summary")
async def get_summary():
    """Get strategy summary report data"""
    try:
        csv_path = os.path.join(PROJECT_ROOT, "data", "summary_report.csv")
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Summary data not found")
        
        df = pd.read_csv(csv_path)
        return df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/analysis/weights")
async def get_weights():
    """Get strategy weights data"""
    try:
        json_path = os.path.join(PROJECT_ROOT, "data", "weight_table.json")
        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail="Weights data not found")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            weights = json.load(f)
        return weights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the server when this script is executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting API server on port {port}")
    print(f"API URLs:")
    print(f"  - http://localhost:{port}/v1/analysis/summary")
    print(f"  - http://localhost:{port}/v1/analysis/weights")
    print(f"  - http://localhost:{port}/docs (API documentation)")
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
    chmod +x runtime_api_server.py
fi

# Start the API server in the background
python runtime_api_server.py > "$API_LOG_FILE" 2>&1 &
SERVER_PID=$!

log "API server started with PID: $SERVER_PID"
log "API URLs:"
log "  - http://localhost:$PORT/v1/analysis/summary"
log "  - http://localhost:$PORT/v1/analysis/weights"
log "  - http://localhost:$PORT/docs (API documentation)"

# Wait for the server to start
sleep 3

# Step 4: Test the API endpoints
log "Step 4: Testing the API endpoints..."

# Function to test an endpoint
test_endpoint() {
    local endpoint=$1
    local name=$2
    log "Testing $name endpoint: http://localhost:$PORT$endpoint"
    
    # Try up to 3 times
    for i in {1..3}; do
        response=$(curl -s -o response.json -w "%{http_code}" "http://localhost:$PORT$endpoint")
        
        if [[ $response -eq 200 ]]; then
            log "✅ $name endpoint is working (HTTP 200)"
            log "Sample response: $(head -n 10 response.json | sed 's/^/  /')"
            rm response.json
            return 0
        else
            log "Attempt $i: $name endpoint returned HTTP $response"
            sleep 2
        fi
    done
    
    log "❌ $name endpoint is not working after 3 attempts"
    [[ -f response.json ]] && log "Error response: $(cat response.json)" && rm response.json
    return 1
}

# Test both endpoints
test_endpoint "/v1/analysis/summary" "Summary"
test_endpoint "/v1/analysis/weights" "Weights"

# Run the more comprehensive test script if available
if [[ -f "test_api.py" ]]; then
    log "Running comprehensive API test script..."
    python test_api.py http://localhost:$PORT >> "$LOG_FILE" 2>&1
    if [[ $? -eq 0 ]]; then
        log "✅ Comprehensive API tests passed"
    else
        log "❌ Some API tests failed. Check the log for details."
    fi
fi

# Step 5: Open the documentation in a browser
log "Step 5: Opening API documentation in browser..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "http://localhost:$PORT/docs"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "http://localhost:$PORT/docs" &> /dev/null
fi

# Step 6: Start the frontend if available
if [[ -d "web_dashboard" && -f "web_dashboard/package.json" ]]; then
    log "Step 6: Found web dashboard, checking if we can start it..."
    
    if command -v npm &> /dev/null; then
        log "npm is available, let's check if we need to install dependencies"
        
        (
            cd web_dashboard
            if [[ ! -d "node_modules" ]]; then
                log "Installing web dashboard dependencies..."
                npm install
            fi
            
            log "Starting web dashboard..."
            echo "PORT=3000 REACT_APP_API_URL=http://localhost:$PORT npm start"
            PORT=3000 REACT_APP_API_URL="http://localhost:$PORT" npm start &
            DASHBOARD_PID=$!
            log "Web dashboard started with PID: $DASHBOARD_PID"
            log "Web dashboard available at: http://localhost:3000"
        )
    else
        log "npm is not available. Skipping web dashboard startup."
        log "To start the web dashboard manually:"
        log "  cd web_dashboard"
        log "  npm install (if needed)"
        log "  PORT=3000 REACT_APP_API_URL=http://localhost:$PORT npm start"
    fi
else
    log "Web dashboard not found in the expected location."
fi

# Display a summary
log "==================================================="
log "System is now running!"
log "==================================================="
log "API server running on: http://localhost:$PORT"
log "API endpoints:"
log "  - http://localhost:$PORT/v1/analysis/summary"
log "  - http://localhost:$PORT/v1/analysis/weights"
log "  - http://localhost:$PORT/docs (API documentation)"
if [[ -d "web_dashboard" && -f "web_dashboard/package.json" ]]; then
    log "Web dashboard: http://localhost:3000 (if started)"
fi
log "==================================================="
log "Press Ctrl+C to stop the system"

# Wait for Ctrl+C
trap "log 'Shutting down...'; kill $SERVER_PID 2>/dev/null; [[ -n \$DASHBOARD_PID ]] && kill \$DASHBOARD_PID 2>/dev/null; log 'System stopped'; exit 0" INT TERM

# Keep the script running and display server logs
log "Showing API server logs (Press Ctrl+C to stop):"
tail -f "$API_LOG_FILE"
