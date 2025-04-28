# app/app_config.py
import os
import sys
import logging
import importlib.resources as pkg_resources
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("skinnerbox")

def get_project_root():
    """
    Get the root directory of the project, working both in development and when installed as a package
    """
    if getattr(sys, 'frozen', False):
        # We are running in a bundle
        return os.path.dirname(sys.executable)
    else:
        # Try to detect if we're installed in a package or running from source
        try:
            # When installed as a package
            import skinnerbox_source
            return os.path.dirname(os.path.dirname(skinnerbox_source.__file__))
        except ImportError:
            # When running from source
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Get project root directory
project_directory = get_project_root()
logger.info(f"Project directory: {project_directory}")

# Define paths relative to project root
settings_path = os.path.join(project_directory, 'trial_config.json')
log_directory = os.path.join(project_directory, 'logs')
temp_directory = os.path.join(project_directory, 'temp')
gpioMonitor_directory = os.path.join(project_directory, 'gpioMonitor.json')

# Ensure directories exist
for directory in [log_directory, temp_directory]:
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        # Try to create in user's home directory as fallback
        fallback_dir = os.path.join(os.path.expanduser("~"), os.path.basename(directory))
        try:
            if not os.path.exists(fallback_dir):
                os.makedirs(fallback_dir)
            logger.warning(f"Using fallback directory: {fallback_dir}")
            if directory == log_directory:
                log_directory = fallback_dir
            elif directory == temp_directory:
                temp_directory = fallback_dir
        except Exception as inner_e:
            logger.critical(f"Failed to create fallback directory {fallback_dir}: {inner_e}")