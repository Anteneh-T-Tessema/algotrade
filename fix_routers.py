#!/usr/bin/env python3
"""
Quick script to fix router variable names in all router files
"""

import os
import shutil
import sys
import re  # Add the missing import for regex operations

# Router files to fix and their router names
router_files = {
    "trading.py": "trading_router",
    "exchanges.py": "exchange_router",
    "distributor.py": "distributor_router",
    "settings.py": "settings_router",
}

# Get the project directory
script_dir = os.path.dirname(os.path.abspath(__file__))
router_dir = os.path.join(script_dir, "web_dashboard", "server", "routers")

print(f"Looking for router files in: {router_dir}")

# Process each file
for filename, router_var in router_files.items():
    filepath = os.path.join(router_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
        
    print(f"Processing file: {filepath}")
    
    # Read the file content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Store original content for comparison
    original_content = content
    
    print(f"File size before changes: {len(content)} bytes")
    
    # Replace router variable name
    updated_content = re.sub(
        r'router = APIRouter\(',
        f'{router_var} = APIRouter(',
        content
    )
    
    # Replace all @router decorators
    updated_content = re.sub(
        r'@router\.',
        f'@{router_var}.',
        updated_content
    )
    
    # Remove any line that assigns the export variable to router
    updated_content = re.sub(
        fr'{router_var} = router(\n|$)',
        '',
        updated_content
    )
    
    # Count replacements
    decorator_replacements = len(re.findall(fr'@{router_var}\.', updated_content)) - len(re.findall(fr'@{router_var}\.', content))
    print(f"Decorator replacements in {filename}: {decorator_replacements}")
    
    # Only write if changes were made
    if original_content != updated_content:
        # Write the updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated {filename}, file size now: {len(updated_content)} bytes")
    else:
        print(f"No changes needed for {filename}")
print("Router fixes completed!")
