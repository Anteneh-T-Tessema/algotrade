from fastapi import APIRouter, HTTPException
import pandas as pd
import os
import json

analysis_router = APIRouter(
    prefix="/analysis",
    tags=["analysis"]
)

@analysis_router.get("/summary")
async def get_summary_report():
    """
    Get aggregated strategy summary report as JSON
    """
    try:
        # Determine base project directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base_dir, 'data', 'summary_report.csv')
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
            
        return records
    except Exception as e:
        print(f"Error in get_summary_report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.get("/weights")
async def get_weight_table():
    """
    Get dynamic weight table for ensemble strategy per market type
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, 'data', 'weight_table.json')
        
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Weight table file not found")
            
        with open(path, 'r') as f:
            try:
                weights = json.load(f)
                return weights
            except json.JSONDecodeError as je:
                print(f"JSON decode error: {str(je)}")
                raise HTTPException(status_code=500, detail=f"Invalid JSON in weights file: {str(je)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_weight_table: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
