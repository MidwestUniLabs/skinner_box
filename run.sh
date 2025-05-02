#!/bin/bash

# Change to the correct directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the main application using the installed package
python -m skinnerbox.main

# Alternative method if the module approach doesn't work
# python -c "import skinnerbox; skinnerbox.main()"