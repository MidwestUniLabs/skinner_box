"""
Skinner Box - Experiment control system for operant conditioning chambers
"""

import os

# Get the current version from version.txt at the project root
try:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version.txt'), 'r') as f:
        __version__ = f.read().strip()
except FileNotFoundError:
    __version__ = "0.0.0"

# Make the main module accessible at the package level for cleaner imports
from skinnerbox.main import main