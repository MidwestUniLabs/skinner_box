#!/bin/bash

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Check if virtual environment folder exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install packages from requirements.txt
echo "Installing packages from requirements.txt..."
pip install -r requirements.txt

# Install the skinnerbox package in development mode
echo "Installing skinnerbox package in development mode..."
pip install -e .

# Create update checker script
echo "Creating update checker script..."
cat > update_checker.py << 'EOL'
#!/usr/bin/env python3
import requests
import json
import subprocess
import os
import sys

# Get the name of the package from requirements.txt
def get_package_name():
    with open('requirements.txt', 'r') as f:
        # Assuming the first line in requirements.txt is the package name
        # Usually it would be in the format: package_name==version
        first_line = f.readline().strip()
        return first_line.split('==')[0]

def check_for_updates():
    package_name = get_package_name()
    
    # Get current installed version
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package_name],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                current_version = line.split(':', 1)[1].strip()
                break
        else:
            print(f"Could not determine current version of {package_name}")
            return
    except Exception as e:
        print(f"Error getting current version: {e}")
        return
    
    # Get latest version from PyPI
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        if response.status_code == 200:
            data = response.json()
            latest_version = data['info']['version']
            
            print(f"Current version: {current_version}")
            print(f"Latest version: {latest_version}")
            
            if current_version != latest_version:
                print(f"Update available for {package_name}! New version: {latest_version}")
                
                # Here you can add code to automatically update if desired
                # For example: subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', package_name])
            else:
                print(f"{package_name} is up to date.")
        else:
            print(f"Failed to check PyPI. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error checking for updates: {e}")

if __name__ == "__main__":
    check_for_updates()
EOL

# Make the update checker executable
chmod +x update_checker.py
chmod +x

# Setup cron job automatically
echo "Setting up automatic update checks via cron..."
CURRENT_DIR=$(pwd)
PYTHON_PATH=$(which python3)
CRON_JOB="0 0 * * * cd $CURRENT_DIR && $PYTHON_PATH $CURRENT_DIR/update_checker.py >> $CURRENT_DIR/update_log.txt 2>&1"

# Check if cron job already exists to avoid duplicates
CRON_CHECK=$(crontab -l 2>/dev/null | grep -F "$CURRENT_DIR/update_checker.py")
if [ -z "$CRON_CHECK" ]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "# Added by installer.sh for skinner_box update checking"; echo "$CRON_JOB") | crontab -
    echo "Cron job set up successfully. Updates will be checked daily at midnight."
else
    echo "Cron job for update checking already exists."
fi

echo ""
echo "To manually check for updates at any time, run:"
echo "  cd $(pwd) && ./update_checker.py"
echo ""

# Deactivate virtual environment
deactivate

echo "Installation complete!"
