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

# Deactivate virtual environment
deactivate

echo "Installation complete!"
