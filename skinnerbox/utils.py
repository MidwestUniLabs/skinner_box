"""
Utility functions for the Skinner Box application
"""
from datetime import datetime
import json
import os
from skinnerbox.app import app_config


def list_log_files_sorted(log_directory):
    """Sort log files by date in descending order"""
    files = [f for f in os.listdir(log_directory) 
             if os.path.isfile(os.path.join(log_directory, f)) and f.startswith("log_")]
    # Sort the files by date in descending order
    files.sort(key=lambda x: datetime.strptime(x, "log_%m_%d_%y_%H_%M_%S.json"), reverse=True)
    return files


def load_settings():
    """Load settings from the configuration file"""
    try:
        with open(app_config.settings_path, 'r') as file:
            settings = json.load(file)
    except FileNotFoundError:
        settings = {}
    return settings


def save_settings(settings):
    """Save settings to the configuration file"""
    with open(app_config.settings_path, 'w') as file:
        json.dump(settings, file, indent=4)