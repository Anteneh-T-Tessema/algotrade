#!/usr/bin/env python3
"""
Strategy Testing Script Runner

This script runs the test_all_strategies.py script with enhanced error handling
and ensures all results are properly stored for analysis.
"""

import os
import sys
import logging
import traceback
import subprocess
import json
from datetime import datetime

# Configure logging
def setup_logger():
    """Set up a logger for the test runner"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'strategy_test_runner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logger = logging.getLogger('test_runner')
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def ensure_results_dir():
    """Ensure the results directory exists"""
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'results')
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

def run_strategy_tests():
    """Run the strategy tests with error handling"""
    logger = setup_logger()
    results_dir = ensure_results_dir()
    
    logger.info("Starting strategy tests...")
    
    try:
        # Run the test script as a subprocess to capture output
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_all_strategies.py')
        
        # Ensure the script is executable
        if not os.access(script_path, os.X_OK):
            logger.info(f"Making {script_path} executable")
            os.chmod(script_path, 0o755)
        
        logger.info(f"Running {script_path}")
        
        # Run with Python to ensure proper environment
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Capture output
        stdout, stderr = process.communicate()
        
        # Log the output
        logger.info("Test output:")
        for line in stdout.splitlines():
            logger.info(line)
        
        if stderr:
            logger.warning("Errors encountered:")
            for line in stderr.splitlines():
                logger.warning(line)
        
        # Check for created plot files
        plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'plots')
        if os.path.exists(plots_dir):
            plot_files = os.listdir(plots_dir)
            logger.info(f"Generated {len(plot_files)} plot files")
        
        # Check for test log file
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'strategy_test.log')
        if os.path.exists(log_file):
            logger.info(f"Test log file created at {log_file}")
            
            # Extract metrics from log and save to results folder
            try:
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    
                # Parse results for each strategy and market type
                strategy_results = {}
                for line in log_content.splitlines():
                    if "Results for" in line and "on" in line:
                        parts = line.split("Results for ")[1].split(" on ")
                        if len(parts) == 2:
                            strategy = parts[0].strip()
                            market_type = parts[1].strip().rstrip(":")
                            
                            if strategy not in strategy_results:
                                strategy_results[strategy] = {}
                                
                            if market_type not in strategy_results[strategy]:
                                strategy_results[strategy][market_type] = {}
                    
                    # Extract metrics
                    elif "Total Return:" in line:
                        try:
                            value = float(line.split("Total Return:")[1].strip().rstrip("%"))
                            if strategy and market_type:
                                strategy_results[strategy][market_type]['total_return'] = value
                        except:
                            pass
                            
                    elif "Win Rate:" in line:
                        try:
                            value = float(line.split("Win Rate:")[1].strip().rstrip("%")) / 100
                            if strategy and market_type:
                                strategy_results[strategy][market_type]['win_rate'] = value
                        except:
                            pass
                            
                    elif "Sharpe Ratio:" in line:
                        try:
                            value = float(line.split("Sharpe Ratio:")[1].strip())
                            if strategy and market_type:
                                strategy_results[strategy][market_type]['sharpe_ratio'] = value
                        except:
                            pass
                
                # Save results to JSON files
                for strategy, markets in strategy_results.items():
                    for market_type, metrics in markets.items():
                        result_file = os.path.join(results_dir, f"{strategy}_{market_type}.json")
                        
                        result_data = {
                            'strategy_name': strategy,
                            'market_type': market_type,
                            'timestamp': datetime.now().isoformat(),
                            **metrics
                        }
                        
                        with open(result_file, 'w') as f:
                            json.dump(result_data, f, indent=2)
                            
                        logger.info(f"Saved results to {result_file}")
                            
            except Exception as e:
                logger.error(f"Error extracting metrics from log: {str(e)}")
                logger.error(traceback.format_exc())
        
        logger.info("Strategy tests completed")
        return process.returncode == 0
        
    except Exception as e:
        logger.error(f"Error running strategy tests: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = run_strategy_tests()
    sys.exit(0 if success else 1)
