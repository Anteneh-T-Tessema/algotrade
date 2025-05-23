#!/usr/bin/env python3
"""
Run the FastAPI server for the web dashboard.

This script starts the API server that powers the web dashboard.
"""

import os
import sys
import uvicorn

# Add parent directory to path to allow relative imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Development settings
    dev_mode = os.environ.get("NODE_ENV") == "development"
    
    # Print server info
    print(f"🚀 Starting {'development' if dev_mode else 'production'} server on port {port}")
    print("📡 WebSocket endpoints available at:")
    print(f"   - ws://localhost:{port}/v1/ws/market/{{client_id}}")
    print(f"   - ws://localhost:{port}/v1/ws/orderbook/{{client_id}}")
    print(f"   - ws://localhost:{port}/v1/ws/portfolio/{{client_id}}")
    print(f"   - ws://localhost:{port}/v1/ws/trades/{{client_id}}")
    print("\n💻 API available at:")
    print(f"   - http://localhost:{port}/v1/")
    print(f"   - http://localhost:{port}/docs (Swagger UI)\n")
    
    # Start server
    uvicorn.run("server.main:app", 
                host="0.0.0.0", 
                port=port, 
                reload=dev_mode,  # Enable hot reload in development
                log_level="info")
