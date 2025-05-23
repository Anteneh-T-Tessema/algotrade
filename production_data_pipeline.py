#!/usr/bin/env python3
"""
Production data pipeline for strategy analysis.
This script:
1. Processes backtest results
2. Generates summary reports
3. Calculates strategy weights
4. Stores results in structured format

Can be run on a schedule or triggered by new data.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/data_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("data-pipeline")

# Get the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
OUTPUT_DIR = DATA_DIR  # Where to store processed outputs

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "archive"), exist_ok=True)

class DataPipeline:
    """Data pipeline for processing strategy results and generating reports"""
    
    def __init__(self):
        self.summary_data = None
        self.weight_table = None
    
    def process_results(self):
        """Process all strategy backtest results"""
        logger.info("Starting strategy results processing")
        
        try:
            # Step 1: Load and combine results
            raw_results = self._load_backtest_results()
            logger.info(f"Loaded {len(raw_results)} raw result files")
            
            # Step 2: Clean and transform data
            self.summary_data = self._generate_summary_report(raw_results)
            logger.info(f"Generated summary report with {len(self.summary_data)} entries")
            
            # Step 3: Calculate strategy weights
            self.weight_table = self._calculate_weights(self.summary_data)
            logger.info(f"Generated weight table for {len(self.weight_table)} market types")
            
            # Step 4: Save processed data
            self._save_processed_data()
            logger.info("Successfully saved all processed data")
            
            # Step 5: Archive raw results (optional)
            # self._archive_raw_results()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in data pipeline: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _load_backtest_results(self) -> List[Dict]:
        """Load all backtest result files"""
        results = []
        
        if not os.path.exists(RESULTS_DIR):
            logger.warning(f"Results directory not found: {RESULTS_DIR}")
            return results
            
        for filename in os.listdir(RESULTS_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(RESULTS_DIR, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        results.append(data)
                except Exception as e:
                    logger.error(f"Error loading {filename}: {str(e)}")
        
        return results
    
    def _generate_summary_report(self, results: List[Dict]) -> pd.DataFrame:
        """Generate summary report from backtest results"""
        if not results:
            logger.warning("No results to process for summary report")
            # Return an empty DataFrame with the expected structure
            return pd.DataFrame({
                'strategy': [], 
                'market_type': [], 
                'total_return': [], 
                'win_rate': [], 
                'sharpe_ratio': [], 
                'max_drawdown_pct': []
            })
        
        # Extract key metrics from each result
        summary_records = []
        
        for result in results:
            try:
                # Extract the core metrics
                record = {
                    'strategy': result.get('strategy', 'Unknown'),
                    'market_type': result.get('market_type', 'Unknown'),
                    'total_return': float(result.get('performance', {}).get('total_return', 0.0)),
                    'win_rate': float(result.get('performance', {}).get('win_rate', 0.0)),
                    'sharpe_ratio': float(result.get('performance', {}).get('sharpe_ratio', 0.0)),
                    'max_drawdown_pct': result.get('performance', {}).get('max_drawdown_pct')
                }
                summary_records.append(record)
            except Exception as e:
                logger.error(f"Error processing result: {str(e)}")
        
        # Create DataFrame
        df = pd.DataFrame(summary_records)
        
        # Handle special values (inf, -inf, NaN)
        df = df.replace([np.inf, -np.inf], np.nan)
        
        return df
    
    def _calculate_weights(self, summary_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate strategy weights for each market type"""
        if summary_df.empty:
            logger.warning("No data to calculate weights")
            return {}
            
        # Group by market type
        market_types = summary_df['market_type'].unique()
        all_strategies = summary_df['strategy'].unique()
        
        weight_table = {}
        
        for market_type in market_types:
            market_data = summary_df[summary_df['market_type'] == market_type]
            
            # Initialize weights for all strategies
            weights = {strategy: 0.0 for strategy in all_strategies}
            
            # Calculate weights based on performance metrics
            # Use a combined score based on multiple metrics
            if not market_data.empty:
                # Calculate a score for each strategy (simplified example)
                market_data['score'] = (
                    market_data['total_return'] + 
                    market_data['win_rate'] + 
                    market_data['sharpe_ratio']
                )
                
                # Handle negative scores
                market_data['score'] = market_data['score'].apply(
                    lambda x: max(0, x)  # Ensure non-negative scores
                )
                
                total_score = market_data['score'].sum()
                
                # Calculate proportional weights
                if total_score > 0:
                    for _, row in market_data.iterrows():
                        strategy = row['strategy']
                        score = row['score']
                        weights[strategy] = score / total_score
            
            weight_table[market_type] = weights
        
        return weight_table
    
    def _save_processed_data(self):
        """Save processed data to output files"""
        # Save summary report
        if self.summary_data is not None:
            summary_path = os.path.join(OUTPUT_DIR, "summary_report.csv")
            self.summary_data.to_csv(summary_path, index=False)
            logger.info(f"Saved summary report to {summary_path}")
        
        # Save weight table
        if self.weight_table is not None:
            weights_path = os.path.join(OUTPUT_DIR, "weight_table.json")
            with open(weights_path, 'w', encoding='utf-8') as f:
                json.dump(self.weight_table, f, indent=2)
            logger.info(f"Saved weight table to {weights_path}")
    
    def _archive_raw_results(self):
        """Archive raw result files after processing"""
        archive_dir = os.path.join(DATA_DIR, "archive", 
                                 datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(archive_dir, exist_ok=True)
        
        for filename in os.listdir(RESULTS_DIR):
            if filename.endswith('.json'):
                src_path = os.path.join(RESULTS_DIR, filename)
                dst_path = os.path.join(archive_dir, filename)
                try:
                    # Copy to archive and delete original
                    with open(src_path, 'r') as src, open(dst_path, 'w') as dst:
                        dst.write(src.read())
                    os.remove(src_path)
                    logger.debug(f"Archived {filename}")
                except Exception as e:
                    logger.error(f"Error archiving {filename}: {str(e)}")

def main():
    """Main execution function"""
    logger.info("Starting strategy data pipeline")
    
    pipeline = DataPipeline()
    success = pipeline.process_results()
    
    if success:
        logger.info("Data pipeline completed successfully")
        return 0
    else:
        logger.error("Data pipeline failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Unhandled exception in data pipeline: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
