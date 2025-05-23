#!/usr/bin/env python3
"""
Combined script that:
1. Runs the analysis notebook to generate the data files
2. Starts a simple FastAPI server to serve the data
"""

import os
import sys
import subprocess
import json
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Get the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def run_analysis_notebook():
    """Run the analysis notebook to generate summary and weights files"""
    print("Running analysis notebook to generate data files...")
    subprocess.run(
        [
            "jupyter", "nbconvert", 
            "--to", "python", 
            "--execute", "strategy_results_analysis.ipynb",
            "--output", "tmp_analysis.py"
        ], 
        check=True
    )
    print("Notebook execution complete")

    # Verify files exist
    summary_file = os.path.join(PROJECT_ROOT, "data", "summary_report.csv")
    weights_file = os.path.join(PROJECT_ROOT, "data", "weight_table.json")
    
    if os.path.exists(summary_file):
        print(f"Summary file exists: {summary_file}")
    else:
        print(f"ERROR: Summary file not found: {summary_file}")
    
    if os.path.exists(weights_file):
        print(f"Weights file exists: {weights_file}")
    else:
        print(f"ERROR: Weights file not found: {weights_file}")

def create_api_server():
    """Create and configure the FastAPI server"""
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
    
    return app

def main():
    """Main function to run the analysis and start the server"""
    try:
        # Step 1: Run the analysis notebook
        run_analysis_notebook()
        
        # Step 2: Create and start the API server
        app = create_api_server()
        
        # Print info
        print("\n" + "="*50)
        print("Starting FastAPI server...")
        print("API will be available at:")
        print("  - http://localhost:8000/v1/analysis/summary")
        print("  - http://localhost:8000/v1/analysis/weights")
        print("  - http://localhost:8000/docs (API documentation)")
        print("="*50 + "\n")
        
        # Start the server
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
