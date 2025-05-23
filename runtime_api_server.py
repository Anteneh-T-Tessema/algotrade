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
        
        # Read CSV with explicit handling of missing values
        df = pd.read_csv(csv_path)
        
        # Convert to records, handling special values
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val) or pd.isnull(val):
                    record[col] = None
                elif isinstance(val, float) and (val == float('inf') or val == float('-inf')):
                    record[col] = str(val)  # Convert inf/-inf to strings
                else:
                    record[col] = val
            records.append(record)
            
        print(f"Processed {len(records)} records successfully")
        return records
        
    except Exception as e:
        print(f"Error in get_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/analysis/weights")
async def get_weights():
    """Get strategy weights data"""
    try:
        json_path = os.path.join(PROJECT_ROOT, "data", "weight_table.json")
        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail="Weights data not found")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                weights = json.load(f)
                return weights
            except json.JSONDecodeError as je:
                print(f"JSON decode error: {str(je)}")
                raise HTTPException(status_code=500, detail=f"Invalid JSON in weights file: {str(je)}")
    except Exception as e:
        print(f"Error in get_weights: {str(e)}")
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
