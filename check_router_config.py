#!/usr/bin/env python3
"""
Script to verify that the analysis router is correctly wired up in the FastAPI app.
"""
import os
import sys
import inspect

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

print("Checking FastAPI routers configuration...")
print(f"Project root: {project_root}")

try:
    # Import the analysis router
    print("\nImporting analysis_router...")
    from web_dashboard.server.routers.analysis import analysis_router
    print(f"Successfully imported analysis_router: {analysis_router}")
    print(f"Router prefix: {analysis_router.prefix}")
    print(f"Router routes: {len(analysis_router.routes)}")
    for route in analysis_router.routes:
        print(f"  - {route.path}: {route.name}")
    
    # Import the API router
    print("\nImporting api_router...")
    from web_dashboard.server.routers import api_router
    print(f"Successfully imported api_router: {api_router}")
    
    # Check if analysis_router is included in api_router
    print("\nChecking if analysis_router is included in api_router...")
    included = False
    for router in api_router.routes:
        if hasattr(router, 'prefix') and router.prefix == '/analysis':
            included = True
            print(f"Found analysis router in api_router: {router}")
    if not included:
        print("WARNING: analysis_router is NOT included in api_router!")
    else:
        print("SUCCESS: analysis_router is included in api_router")
    
    # Import the FastAPI app
    print("\nImporting the FastAPI app...")
    from web_dashboard.server.main import app
    print(f"Successfully imported app: {app}")
    
    # Check if api_router is included in app
    print("\nRoutes registered in the FastAPI app:")
    for route in app.routes:
        print(f"  - {route.path}")
    
    # Check endpoints specific to our needs
    print("\nChecking for our specific endpoints...")
    endpoints = ['/v1/analysis/summary', '/v1/analysis/weights']
    for endpoint in endpoints:
        found = False
        for route in app.routes:
            if route.path == endpoint:
                found = True
                print(f"Found endpoint {endpoint}: {route}")
                break
        if not found:
            print(f"WARNING: endpoint {endpoint} NOT found in app!")
        else:
            print(f"SUCCESS: endpoint {endpoint} found in app")
    
    print("\nRouter check completed successfully")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
