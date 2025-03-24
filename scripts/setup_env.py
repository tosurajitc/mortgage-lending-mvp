#!/usr/bin/env python
"""
Setup environment script for the Mortgage Lending MVP.

This script creates a .env file from the .env.example template,
prompting the user for values to replace placeholders.
"""

import os
import sys
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a secure random key for JWT signing."""
    return secrets.token_hex(32)

def main():
    # Get the project root directory
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Path to the template and target files
    template_path = project_root / ".env.example"
    env_file_path = project_root / ".env"
    
    # Check if template exists
    if not template_path.exists():
        print(f"Error: Template file not found at {template_path}")
        sys.exit(1)
    
    # Check if .env already exists
    if env_file_path.exists():
        overwrite = input(".env file already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    # Read the template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Process the template line by line
    new_content = []
    for line in template_content.splitlines():
        # Skip comments and empty lines
        if line.startswith("#") or not line.strip():
            new_content.append(line)
            continue
        
        # Process key-value pairs
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Generate a secret key automatically
        if key == "SECRET_KEY":
            value = generate_secret_key()
            print(f"Generated a new secret key")
        # Ask the user for values that look like placeholders
        elif value.startswith('your_') or 'your-' in value:
            new_value = input(f"Enter value for {key} [{value}]: ")
            if new_value:
                value = new_value
            
        new_content.append(f"{key}={value}")
    
    # Write the new .env file
    with open(env_file_path, 'w') as f:
        f.write('\n'.join(new_content))
    
    print(f".env file created at {env_file_path}")
    print("You can edit this file later as needed.")

if __name__ == "__main__":
    main()