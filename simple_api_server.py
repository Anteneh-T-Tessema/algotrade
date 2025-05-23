# Quick fix to patch the API router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a minimal app
app = FastAPI(title="Analysis API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Analysis endpoints
@app.get("/v1/analysis/summary")
async def get_summary():
    """Get summary data"""
    import os
    import pandas as pd
    
    # Path to CSV
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'data', 'summary_report.csv')
    
    # Read CSV
    df = pd.read_csv(csv_path)
    return df.to_dict(orient='records')

@app.get("/v1/analysis/weights")
async def get_weights():
    """Get weights data"""
    import os
    import json
    
    # Path to JSON
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'data', 'weight_table.json')
    
    # Read JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        weights = json.load(f)
    return weights

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
