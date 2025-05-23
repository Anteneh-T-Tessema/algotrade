#!/usr/bin/env python3
"""
Test script for the strategy analysis API server
"""
import requests
import json
import sys
import time
import os
from pprint import pprint

def test_api_endpoints(base_url="http://localhost:8000"):
    """Test the API endpoints"""
    print(f"Testing API at {base_url}")
    
    # Test the summary endpoint
    print("\n--- Testing /v1/analysis/summary endpoint ---")
    try:
        response = requests.get(f"{base_url}/v1/analysis/summary")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary endpoint works: {len(data)} records retrieved")
            # Print a sample record
            if data:
                print("\nSample summary record:")
                pprint(data[0])
        else:
            print(f"❌ Summary endpoint failed with status code {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception when testing summary endpoint: {str(e)}")
    
    # Test the weights endpoint
    print("\n--- Testing /v1/analysis/weights endpoint ---")
    try:
        response = requests.get(f"{base_url}/v1/analysis/weights")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Weights endpoint works: Data for {len(data)} market types retrieved")
            # Print a sample market type
            if data:
                market_type = next(iter(data))
                print(f"\nSample weight data for '{market_type}':")
                pprint(data[market_type])
        else:
            print(f"❌ Weights endpoint failed with status code {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception when testing weights endpoint: {str(e)}")
    
    # Test the documentation endpoint
    print("\n--- Testing /docs endpoint ---")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ Documentation endpoint works")
        else:
            print(f"❌ Documentation endpoint failed with status code {response.status_code}")
    except Exception as e:
        print(f"❌ Exception when testing docs endpoint: {str(e)}")

if __name__ == "__main__":
    # If a command-line argument is provided, use it as the base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Test the API endpoints
    test_api_endpoints(base_url)
