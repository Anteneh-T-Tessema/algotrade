#!/usr/bin/env python3
"""
Script to directly edit each router file to fix routing issues
"""

import os
import sys

def fix_settings_router():
    file_path = "/Users/antenehtessema/Desktop/botsalgo/web_dashboard/server/routers/settings.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all occurrences of @router. with @settings_router.
    content = content.replace('@router.', '@settings_router.')
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed settings.py")

def fix_distributor_router():
    file_path = "/Users/antenehtessema/Desktop/botsalgo/web_dashboard/server/routers/distributor.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all occurrences of @router. with @distributor_router.
    content = content.replace('@router.', '@distributor_router.')
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed distributor.py")

def fix_exchanges_router():
    file_path = "/Users/antenehtessema/Desktop/botsalgo/web_dashboard/server/routers/exchanges.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all occurrences of @router. with @exchange_router.
    content = content.replace('@router.', '@exchange_router.')
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed exchanges.py")

if __name__ == "__main__":
    print("Fixing router files...")
    fix_settings_router()
    fix_distributor_router()
    fix_exchanges_router()
    print("All router files fixed!")
