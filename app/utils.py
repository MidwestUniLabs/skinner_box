"""
Utility functions for the Skinner Box application
"""
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger("skinnerbox.utils")

def find_package_path(directory_name):
    """
    Find a directory within the package, checking multiple possible locations
    to handle both development and installation scenarios.
    
    Args:
        directory_name (str): Name of directory to find (e.g., 'templates', 'static')
        
    Returns:
        str: Path to the directory if found, None otherwise
    """
    # Start with the current file location and work upwards
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # List of potential locations to check
    potential_paths = [
        # Direct subdirectory of the app package
        os.path.join(current_dir, directory_name),
        
        # Sibling directory to the app package
        os.path.join(parent_dir, directory_name),
        
        # Inside the app package with the same name
        os.path.join(current_dir, directory_name, directory_name)
    ]
    
    # Check each potential path
    for path in potential_paths:
        if os.path.exists(path) and os.path.isdir(path):
            logger.debug(f"Found {directory_name} directory at: {path}")
            return path
            
    logger.warning(f"Could not find {directory_name} directory in any expected location")
    return None

def get_resource_path(resource_type, filename=None):
    """
    Get the path to a resource file, handling both development and installation scenarios.
    
    Args:
        resource_type (str): Type of resource ('templates', 'static', etc.)
        filename (str, optional): Specific filename within the resource directory
        
    Returns:
        str: Path to the resource
    """
    resource_dir = find_package_path(resource_type)
    
    if not resource_dir:
        logger.error(f"Resource directory '{resource_type}' not found")
        return None
        
    if filename:
        resource_path = os.path.join(resource_dir, filename)
        if not os.path.exists(resource_path):
            logger.error(f"Resource file '{filename}' not found in '{resource_type}' directory")
            return None
        return resource_path
    
    return resource_dir