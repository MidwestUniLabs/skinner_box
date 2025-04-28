"""
Skinner Box - A Python package for behavioral experiments
"""
import os
import sys
from pathlib import Path

__version__ = "unknown"
try:
    with open(os.path.join(os.path.dirname(__file__), "version.txt"), "r") as f:
        __version__ = f.read().strip()
except FileNotFoundError:
    pass

def get_package_root():
    """
    Get the root directory of the package
    """
    return os.path.dirname(__file__)

def get_templates_dir():
    """
    Get the path to the templates directory
    """
    return os.path.join(get_package_root(), "templates")

def get_static_dir():
    """
    Get the path to the static directory
    """
    return os.path.join(get_package_root(), "static")