#!/usr/bin/env python3
"""
End-to-end verification script

This script will:
1. Generate summary and weight data
2. Start the API server
3. Fetch data from the API
4. Test the EnsembleStrategy with the weights

Use this script to verify that all components are working properly
before running the full dashboard.
"""

import os
import sys
import json
import time
import subprocess
import requests
import tempfile
import signal
import pandas as pd
from pathlib import Path
from urllib.parse import urljoin

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Constants
API_BASE_URL = "http://localhost:8000"
SUMMARY_ENDPOINT = "/v1/analysis/summary"
WEIGHTS_ENDPOINT = "/v1/analysis/weights"

# Function to run the analysis notebook and generate data files
def generate_data_files():
    """Run the analysis notebook to generate summary and weight files"""
    print("Step 1: Generating data files from the analysis notebook...")
    
    # Run the notebook
    try:
        cmd = [
            "jupyter", "nbconvert", 
            "--to", "python", 
            "--execute", "strategy_results_analysis.ipynb",
            "--output", "tmp_analysis.py"
        ]
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Notebook execution successful")
    except subprocess.CalledProcessError as e:
        print("Error executing notebook:")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        sys.exit(1)
    
    # Verify files exist
    summary_file = os.path.join(project_root, "data", "summary_report.csv")
    weights_file = os.path.join(project_root, "data", "weight_table.json")
    
    if os.path.exists(summary_file):
        print(f"Summary file exists: {summary_file}")
        # Read a few rows to verify
        try:
            df = pd.read_csv(summary_file)
            print(f"Summary file contains {len(df)} rows")
            if len(df) > 0:
                print("Sample row:")
                print(df.iloc[0])
        except Exception as e:
            print(f"Error reading summary file: {e}")
    else:
        print(f"ERROR: Summary file not found: {summary_file}")
        sys.exit(1)
    
    if os.path.exists(weights_file):
        print(f"Weights file exists: {weights_file}")
        # Read the file to verify
        try:
            with open(weights_file, 'r', encoding='utf-8') as f:
                weights = json.load(f)
            print(f"Weights file contains data for {len(weights)} market types")
            if len(weights) > 0:
                market_type = next(iter(weights))
                print(f"Sample weights for {market_type}:")
                print(weights[market_type])
        except Exception as e:
            print(f"Error reading weights file: {e}")
    else:
        print(f"ERROR: Weights file not found: {weights_file}")
        sys.exit(1)
    
    print("Data files generated successfully")
    print()

# Function to start the API server in a subprocess
def start_api_server():
    """Start the API server in a subprocess"""
    print("Step 2: Starting API server...")
    
    # Create a temporary file to capture the server output
    log_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    print(f"Server logs will be written to: {log_file.name}")
    
    # Run the combined_analysis_server.py script
    server_process = subprocess.Popen(
        [sys.executable, os.path.join(project_root, "simple_api_server.py")], 
        stdout=log_file, 
        stderr=subprocess.STDOUT
    )
    
    # Wait for the server to start
    print("Waiting for server to start...")
    for _ in range(10):
        try:
            response = requests.get(API_BASE_URL, timeout=1)
            print(f"Server is running, got status code: {response.status_code}")
            break
        except requests.exceptions.ConnectionError:
            print(".", end="", flush=True)
            time.sleep(1)
    else:
        print("\nServer did not start properly, check logs")
        server_process.terminate()
        sys.exit(1)
    
    print("API server started successfully")
    print()
    
    return server_process, log_file

# Function to test the API endpoints
def test_api_endpoints():
    """Test the API endpoints by fetching data"""
    print("Step 3: Testing API endpoints...")
    
    # Test summary endpoint
    print(f"Testing endpoint: {urljoin(API_BASE_URL, SUMMARY_ENDPOINT)}")
    try:
        response = requests.get(urljoin(API_BASE_URL, SUMMARY_ENDPOINT), timeout=5)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data)} records from summary endpoint")
            if len(data) > 0:
                print("First record:")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error testing summary endpoint: {e}")
    
    # Test weights endpoint
    print(f"\nTesting endpoint: {urljoin(API_BASE_URL, WEIGHTS_ENDPOINT)}")
    try:
        response = requests.get(urljoin(API_BASE_URL, WEIGHTS_ENDPOINT), timeout=5)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received weights data for {len(data)} market types")
            if len(data) > 0:
                market_type = next(iter(data))
                print(f"Sample weights for {market_type}:")
                print(json.dumps(data[market_type], indent=2))
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error testing weights endpoint: {e}")
    
    print("API endpoint testing completed")
    print()

# Function to create a temporary test script for EnsembleStrategy
def test_ensemble_strategy():
    """Create and run a test script for the EnsembleStrategy"""
    print("Step 4: Testing EnsembleStrategy with the weights data...")
    
    # Create a temporary test script
    temp_script = """
import os
import sys
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Try to import the strategy
try:
    from strategies.ensemble_strategy import EnsembleStrategy
    logger.info("Successfully imported EnsembleStrategy")
except Exception as e:
    logger.error(f"Error importing EnsembleStrategy: {e}")
    sys.exit(1)

# Try to load weights file
try:
    weights_file = os.path.join(project_root, "data", "weight_table.json")
    with open(weights_file, 'r', encoding='utf-8') as f:
        weights = json.load(f)
    logger.info(f"Successfully loaded weights for {len(weights)} market types")
    
    # Show sample weights
    market_type = next(iter(weights))
    logger.info(f"Sample weights for {market_type}:")
    for strategy, weight in weights[market_type].items():
        logger.info(f"  {strategy}: {weight:.4f}")
except Exception as e:
    logger.error(f"Error loading weights: {e}")
    sys.exit(1)

# Try to create an instance of EnsembleStrategy
try:
    ensemble = EnsembleStrategy(
        name="TestEnsemble",
        params={"market_type": market_type},
        strategy_classes={},  # Empty for this test
        weight_table=weights
    )
    logger.info("Successfully created EnsembleStrategy instance")
    
    # Test the weight table access
    test_market = market_type
    test_weights = ensemble.weight_table.get(test_market, {})
    logger.info(f"Retrieved weights for {test_market} from instance:")
    for strategy, weight in test_weights.items():
        logger.info(f"  {strategy}: {weight:.4f}")
    
    logger.info("EnsembleStrategy test completed successfully")
except Exception as e:
    logger.error(f"Error testing EnsembleStrategy: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
"""
    
    # Write the temp script to a file
    temp_file = os.path.join(project_root, "temp_ensemble_test.py")
    with open(temp_file, 'w') as f:
        f.write(temp_script)
    
    # Run the temp script
    try:
        print("Running test script for EnsembleStrategy...")
        process = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            check=True
        )
        print(process.stdout)
    except subprocess.CalledProcessError as e:
        print("Error testing EnsembleStrategy:")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
    finally:
        # Clean up
        os.unlink(temp_file)
    
    print("EnsembleStrategy testing completed")
    print()

# Main function
def main():
    print("="*80)
    print("End-to-End Verification Script")
    print("="*80)
    print()
    
    try:
        # Step 1: Generate data files
        generate_data_files()
        
        # Step 2: Start API server
        server_process, log_file = start_api_server()
        
        try:
            # Step 3: Test API endpoints
            test_api_endpoints()
            
            # Step 4: Test EnsembleStrategy
            test_ensemble_strategy()
            
            # Success
            print("="*80)
            print("VERIFICATION COMPLETED SUCCESSFULLY")
            print("All components are working properly")
            print("="*80)
            
        finally:
            # Clean up
            print("\nCleaning up...")
            if server_process:
                server_process.send_signal(signal.SIGTERM)
                server_process.wait(timeout=5)
                print("Server process terminated")
            
            if log_file:
                log_file_name = log_file.name
                log_file.close()
                print(f"Server log file: {log_file_name}")
                with open(log_file_name, 'r') as f:
                    print("\nServer log contents:")
                    print(f.read())
                os.unlink(log_file_name)
    
    except KeyboardInterrupt:
        print("\nVerification interrupted by user")
    except Exception as e:
        print(f"\nError during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
