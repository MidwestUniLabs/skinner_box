#!/usr/bin/env python3
import requests
import json
import subprocess
import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "update_checker.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("update_checker")

def get_package_name():
    """Get the package name from requirements.txt"""
    try:
        # Try to find requirements.txt in various locations
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt"),
            "requirements.txt"  # Current working directory
        ]
        
        for req_path in possible_paths:
            if os.path.exists(req_path):
                with open(req_path, 'r') as f:
                    requirements = f.readlines()
                # Look for the package name (assuming it starts with Skinnerbox)
                for req in requirements:
                    if req.strip().lower().startswith("skinnerbox"):
                        return req.strip().split('==')[0]
                
                logger.warning("Package name not found in requirements.txt")
                return "Skinnerbox-Source"  # Default package name
        
        logger.warning("requirements.txt not found, using default package name")
        return "Skinnerbox-Source"  # Default package name
        
    except Exception as e:
        logger.error(f"Error in get_package_name: {e}")
        return "Skinnerbox-Source"  # Default package name

def check_for_updates(auto_update=False):
    """Check if updates are available on PyPI"""
    package_name = get_package_name()
    logger.info(f"Checking for updates for package: {package_name}")
    
    try:
        # Get current version from version.txt
        version_file_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "version.txt"),
            "version.txt"  # Current working directory
        ]
        
        current_version = None
        for version_path in version_file_paths:
            if os.path.exists(version_path):
                with open(version_path, 'r') as f:
                    current_version = f.read().strip()
                break
        
        if current_version is None:
            logger.error("version.txt not found")
            return False
            
        # Get latest version from PyPI
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        if response.status_code != 200:
            logger.error(f"Failed to get package info from PyPI: {response.status_code}")
            return False
            
        latest_version = response.json()['info']['version']
        
        logger.info(f"Current version: {current_version}")
        logger.info(f"Latest version: {latest_version}")
        
        if latest_version != current_version:
            logger.info("Update available!")
            
            if auto_update:
                logger.info("Auto-updating...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', package_name])
                
                if result.returncode == 0:
                    logger.info("Update successful!")
                    return True
                else:
                    logger.error("Update failed.")
                    return False
            else:
                logger.info("Run with --auto-update to install the update automatically.")
                return True
        else:
            logger.info("Already up to date!")
            return False
            
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return False

def setup_cron_job():
    """Set up a cron job to run the update checker daily"""
    # Skip this on Windows
    if sys.platform.startswith('win'):
        logger.info("Cron jobs are not supported on Windows.")
        return False
        
    try:
        script_path = os.path.abspath(__file__)
        cron_line = f"0 0 * * * cd {os.path.dirname(script_path)} && {sys.executable} {script_path} --auto-update >> update_log.txt 2>&1"
        
        # Write to a temporary file
        temp_cron = os.path.join(os.path.dirname(script_path), 'tempcron')
        with open(temp_cron, 'w') as f:
            # Get existing crontab
            try:
                subprocess.run(['crontab', '-l'], stdout=f, stderr=subprocess.DEVNULL)
            except:
                # No existing crontab, that's fine
                pass
                
            f.write(f"\n# Added by update_checker.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(cron_line + "\n")
        
        # Install the new crontab
        subprocess.run(['crontab', temp_cron])
        os.remove(temp_cron)
        
        logger.info("Cron job set up successfully to check for updates daily at midnight")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up cron job: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check for package updates on PyPI')
    parser.add_argument('--auto-update', action='store_true', help='Automatically install updates if available')
    parser.add_argument('--setup-cron', action='store_true', help='Set up a daily cron job to check for updates')
    
    args = parser.parse_args()
    
    if args.setup_cron:
        if setup_cron_job():
            logger.info("Cron job setup successful")
        else:
            logger.error("Failed to setup cron job")
    
    update_available = check_for_updates(args.auto_update)
    sys.exit(0 if not update_available else 1)  # Exit code 1 if update available but not installed