#!/usr/bin/env python3
"""
Simplified runner for the FastAPI server to test the API endpoints.
"""
import os
import sys
import subprocess
import time

# Get the project root
project_root = os.path.dirname(os.path.abspath(__file__))

# Print info
print("Starting FastAPI server...")
print("Server will run at http://localhost:8000")
print("API endpoints should be available at:")
print("  - http://localhost:8000/v1/analysis/summary")
print("  - http://localhost:8000/v1/analysis/weights")
print("  - http://localhost:8000/docs (API documentation)")
print("\nPress Ctrl+C to stop the server\n")

# Execute the server
try:
    os.environ["PORT"] = "8000"
    os.environ["NODE_ENV"] = "development"
    
    # Run the server
    server_dir = os.path.join(project_root, "web_dashboard")
    os.chdir(server_dir)
    
    subprocess.run(
        ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        check=True
    )
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Error running server: {e}")
