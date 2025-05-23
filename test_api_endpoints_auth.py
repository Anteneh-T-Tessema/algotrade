#!/usr/bin/env python3
"""
Test script to verify the web dashboard API endpoints for analysis data
Updated to work with the authentication system
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
    Test the analysis API endpoints with authentication
    """
    # Set up logging to print to console
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    logger = logging.getLogger("api_test")
    
    # Print startup message
    logger.info("Starting API endpoint tests")
    logger.info(f"Testing against server at {base_url}")
    
    # Test if server is running first
    try:
        logger.info("Testing if server is running...")
        response = requests.get(base_url, timeout=3)
        logger.info(f"Server responded with status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to server at {base_url}")
        logger.error("Please ensure the server is running")
        return
    except Exception as e:
        logger.error(f"Unexpected error when connecting to server: {e}")
        return
    
    # Authenticate first to get access token
    admin_credentials = {
        "username": "admin",
        "password": "adminpassword"  # This matches the default admin password
    }
    
    token_url = urljoin(base_url, "/v1/auth/token")
    logger.info(f"Authenticating as admin user: {token_url}")
    
    try:
        token_response = requests.post(
            token_url, 
            data={
                "username": admin_credentials["username"],
                "password": admin_credentials["password"]
            }
        )
        logger.info(f"Authentication response status code: {token_response.status_code}")
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data["access_token"]
            logger.info("Authentication successful")
            
            # Set up headers for authenticated requests
            auth_headers = {"Authorization": f"Bearer {access_token}"}
        else:
            logger.error(f"Failed to authenticate. Status: {token_response.status_code}")
            logger.error(f"Error: {token_response.text}")
            logger.error("Continuing tests without authentication")
            auth_headers = {}
    except Exception as e:
        logger.error(f"Exception during authentication: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("Continuing tests without authentication")
        auth_headers = {}
    
    # Test summary endpoint
    summary_url = urljoin(base_url, "/v1/analysis/summary")
    logger.info(f"Testing endpoint: {summary_url}")
    
    try:
        summary_response = requests.get(summary_url, headers=auth_headers)
        logger.info(f"Response status code: {summary_response.status_code}")
        if summary_response.status_code == 200:
            data = summary_response.json()
            logger.info(f"Summary endpoint successful. Received {len(data)} records.")
            if len(data) > 0:
                logger.info(f"First record: {json.dumps(data[0], indent=2)}")
        else:
            logger.error(f"Failed to get summary data. Status: {summary_response.status_code}")
            logger.error(f"Error: {summary_response.text}")
    except Exception as e:
        logger.error(f"Exception when accessing summary endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Test weights endpoint
    weights_url = urljoin(base_url, "/v1/analysis/weights")
    logger.info(f"Testing endpoint: {weights_url}")
    
    try:
        weights_response = requests.get(weights_url, headers=auth_headers)
        logger.info(f"Response status code: {weights_response.status_code}")
        if weights_response.status_code == 200:
            weights = weights_response.json()
            logger.info(f"Weights endpoint successful. Received data for {len(weights)} market types.")
            for market_type, strategies in weights.items():
                logger.info(f"Market type: {market_type}, Strategies: {len(strategies)}")
        else:
            logger.error(f"Failed to get weights data. Status: {weights_response.status_code}")
            logger.error(f"Error: {weights_response.text}")
    except Exception as e:
        logger.error(f"Exception when accessing weights endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_api_endpoints()
