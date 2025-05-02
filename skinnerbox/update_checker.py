#!/usr/bin/env python3
import requests
import json
import subprocess
import os
import sys
import argparse
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_checker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_package_name():
    """Get the package name from requirements.txt"""
    try:
        with open('requirements.txt', 'r') as f:
            # Assuming the first line in requirements.txt is the package name
            # Usually it would be in the format: package_name==version
            first_line = f.readline().strip()
            return first_line.split('==')[0]
    except FileNotFoundError:
        logger.error("requirements.txt not found")
        return None
    except Exception as e:
        logger.error(f"Error reading requirements.txt: {e}")
        return None

def check_for_updates(auto_update=False):
    """Check if updates are available on PyPI"""
    package_name = get_package_name()
    if not package_name:
        return
    
    logger.info(f"Checking for updates for {package_name}...")
    
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
            logger.error(f"Could not determine current version of {package_name}")
            return
    except Exception as e:
        logger.error(f"Error getting current version: {e}")
        return
    
    # Get latest version from PyPI
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        if response.status_code == 200:
            data = response.json()
            latest_version = data['info']['version']
            
            logger.info(f"Current version: {current_version}")
            logger.info(f"Latest version: {latest_version}")
            
            if current_version != latest_version:
                logger.info(f"Update available for {package_name}! New version: {latest_version}")
                
                if auto_update:
                    logger.info(f"Automatically updating {package_name}...")
                    try:
                        update_result = subprocess.run(
                            [sys.executable, '-m', 'pip', 'install', '--upgrade', package_name],
                            capture_output=True,
                            text=True
                        )
                        logger.info(f"Update result: {update_result.stdout}")
                        if update_result.returncode != 0:
                            logger.error(f"Update failed: {update_result.stderr}")
                    except Exception as e:
                        logger.error(f"Error during update: {e}")
            else:
                logger.info(f"{package_name} is up to date.")
        else:
            logger.error(f"Failed to check PyPI. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")

def setup_cron_job():
    """Set up a cron job to run the update checker daily"""
    try:
        cron_line = f"0 0 * * * cd {os.getcwd()} && {sys.executable} {os.path.abspath(__file__)} >> update_log.txt 2>&1"
        
        # Write to a temporary file
        with open('tempcron', 'w') as f:
            # Get existing crontab
            subprocess.run(['crontab', '-l'], stdout=f, stderr=subprocess.DEVNULL)
            f.write(f"\n# Added by update_checker.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(cron_line + "\n")
        
        # Install the new crontab
        subprocess.run(['crontab', 'tempcron'])
        os.remove('tempcron')
        
        logger.info("Cron job set up successfully to check for updates daily at midnight")
    except Exception as e:
        logger.error(f"Error setting up cron job: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check for package updates on PyPI')
    parser.add_argument('--auto-update', action='store_true', help='Automatically install updates if available')
    parser.add_argument('--setup-cron', action='store_true', help='Set up a daily cron job to check for updates')
    
    args = parser.parse_args()
    
    if args.setup_cron:
        setup_cron_job()
    
    check_for_updates(args.auto_update)