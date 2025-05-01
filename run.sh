#!/bin/bash

# Change to the correct directory
cd /mnt/c/Users/jacob/Documents/GitHub/skinner_box

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi
echo "Running the script..."
# Run the main.py file
python main.py