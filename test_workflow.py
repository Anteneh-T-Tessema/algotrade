#!/usr/bin/env python3
"""
End-to-end test script for the strategy analysis and visualization workflow
"""
import os
import sys
import subprocess
import logging
import time
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("workflow_test")

def run_notebook():
    """Run the analysis notebook to generate data files"""
    logger.info("Running strategy_results_analysis.ipynb to generate data files...")
    try:
        result = subprocess.run(
            [
                "jupyter", "nbconvert", 
                "--to", "python", 
                "--execute", "strategy_results_analysis.ipynb",
                "--output", "tmp_analysis.py"
            ], 
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Successfully executed analysis notebook")
        
        # Check that output files exist
        weight_file = Path("data/weight_table.json")
        summary_file = Path("data/summary_report.csv")
        
        if weight_file.exists() and summary_file.exists():
            logger.info(f"Verified output files exist:")
            logger.info(f"  - {weight_file} ({weight_file.stat().st_size} bytes)")
            logger.info(f"  - {summary_file} ({summary_file.stat().st_size} bytes)")
        else:
            logger.error("One or more output files are missing!")
            if not weight_file.exists():
                logger.error(f"  - {weight_file} is missing")
            if not summary_file.exists():
                logger.error(f"  - {summary_file} is missing")
                
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run notebook: {e}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error: {e.stderr}")
        return False

def start_api_server():
    """Start the FastAPI server in a separate process"""
    logger.info("Starting FastAPI server...")
    
    api_process = subprocess.Popen(
        [sys.executable, "web_dashboard/run_server.py"],
        # No need to capture output
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a bit for the server to start
    logger.info("Waiting for server to start...")
    time.sleep(3)
    
    # Check if process is still running
    if api_process.poll() is None:
        logger.info("Server started successfully")
        return api_process
    else:
        stdout, stderr = api_process.communicate()
        logger.error("Server failed to start")
        logger.error(f"Output: {stdout}")
        logger.error(f"Error: {stderr}")
        return None

def run_api_tests():
    """Run the API endpoint tests"""
    logger.info("Testing API endpoints...")
    try:
        result = subprocess.run(
            [sys.executable, "test_api_endpoints.py"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("API tests completed successfully")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"API tests failed: {e}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error: {e.stderr}")
        return False

def run_ensemble_test():
    """Test the EnsembleStrategy"""
    logger.info("Testing EnsembleStrategy...")
    try:
        result = subprocess.run(
            [sys.executable, "test_ensemble.py"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("EnsembleStrategy test completed successfully")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"EnsembleStrategy test failed: {e}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error: {e.stderr}")
        return False

def main():
    logger.info("Starting end-to-end workflow test")
    
    # Step 1: Run the notebook to generate data
    if not run_notebook():
        logger.error("Notebook execution failed. Aborting further tests.")
        return
    
    # Step 2: Test the EnsembleStrategy
    if not run_ensemble_test():
        logger.warning("EnsembleStrategy test failed, but continuing...")
    
    # Step 3: Start the API server
    api_process = start_api_server()
    if api_process is None:
        logger.error("Failed to start API server. Aborting further tests.")
        return
    
    try:
        # Step 4: Test the API endpoints
        if not run_api_tests():
            logger.warning("API tests failed, but continuing...")
        
        # Step 5: Open the web interface (if available)
        logger.info("Opening web interface at http://localhost:8000/docs")
        webbrowser.open("http://localhost:8000/docs")
        
        # Wait for user to terminate
        logger.info("Press Ctrl+C to terminate the test")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Test terminated by user")
    finally:
        # Clean up
        if api_process and api_process.poll() is None:
            logger.info("Stopping API server...")
            api_process.terminate()
            api_process.wait(timeout=5)
            logger.info("API server stopped")

if __name__ == "__main__":
    main()
