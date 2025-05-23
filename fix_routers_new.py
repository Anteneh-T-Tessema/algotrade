#!/usr/bin/env python3
"""
Script to fix router variable names in all router files
"""

import os
import shutil

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
    
    # Create backup
    backup_path = f"{filepath}.bak"
    shutil.copy2(filepath, backup_path)
    print(f"Created backup at: {backup_path}")
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Replace router variable and decorators
    new_lines = []
    changes = 0
    
    for line in lines:
        # Replace router variable definition
        if line.strip().startswith('router = APIRouter('):
            new_line = line.replace('router = APIRouter(', f'{router_var} = APIRouter(')
            changes += 1
        # Replace router decorators
        elif '@router.' in line:
            new_line = line.replace('@router.', f'@{router_var}.')
            changes += 1
        # Remove redundant export line
        elif line.strip() == f'{router_var} = router':
            new_line = ''
            changes += 1
        else:
            new_line = line
            
        new_lines.append(new_line)
    
    # Write changes back to file
    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Updated {filename} with {changes} changes")
    else:
        print(f"No changes needed for {filename}")
        
print("Router fixes completed!")
