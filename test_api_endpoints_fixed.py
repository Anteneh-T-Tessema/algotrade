#!/usr/bin/env python3
"""
Test script to verify the web dashboard API endpoints for analysis data
"""
import os
import sys
import requests
import json
import logging
from urllib.parse import urljoin

# Ensure the project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def test_api_endpoints(base_url="http://localhost:8000"):
    """
    Test the analysis API endpoints
    """
    # Set up logging to print to console
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    logger = logging.getLogger("api_test")
    
    # Print startup message
    logger.info("Starting API endpoint tests")
    logger.info("Testing against server at %s", base_url)
    
    # Test if server is running first
    try:
        logger.info("Testing if server is running...")
        response = requests.get(base_url, timeout=5)
        logger.info("Server responded with status code: %s", response.status_code)
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to server at %s", base_url)
        logger.error("Please ensure the server is running")
        return
    except requests.exceptions.Timeout:
        logger.error("Connection to server timed out")
        return
    except Exception as e:
        logger.error("Unexpected error when connecting to server: %s", str(e))
        return
    
    # Test summary endpoint
    summary_url = urljoin(base_url, "/v1/analysis/summary")
    logger.info("Testing endpoint: %s", summary_url)
    
    try:
        summary_response = requests.get(summary_url, timeout=5)
        logger.info("Response status code: %s", summary_response.status_code)
        if summary_response.status_code == 200:
            data = summary_response.json()
            logger.info("Summary endpoint successful. Received %d records.", len(data))
            if len(data) > 0:
                logger.info("First record: %s", json.dumps(data[0], indent=2))
        else:
            logger.error("Failed to get summary data. Status: %s", summary_response.status_code)
            logger.error("Error: %s", summary_response.text)
    except requests.exceptions.RequestException as e:
        logger.error("Exception when accessing summary endpoint: %s", str(e))
    
    # Test weights endpoint
    weights_url = urljoin(base_url, "/v1/analysis/weights")
    logger.info("Testing endpoint: %s", weights_url)
    
    try:
        weights_response = requests.get(weights_url, timeout=5)
        logger.info("Response status code: %s", weights_response.status_code)
        if weights_response.status_code == 200:
            weights = weights_response.json()
            logger.info("Weights endpoint successful. Received data for %d market types.", len(weights))
            for market_type, strategies in weights.items():
                logger.info("Market type: %s, Strategies: %d", market_type, len(strategies))
        else:
            logger.error("Failed to get weights data. Status: %s", weights_response.status_code)
            logger.error("Error: %s", weights_response.text)
    except requests.exceptions.RequestException as e:
        logger.error("Exception when accessing weights endpoint: %s", str(e))

if __name__ == "__main__":
    test_api_endpoints()
