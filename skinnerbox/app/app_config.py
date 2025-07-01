# app/app_config.py
import os

# Get project folders directory
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Navigate up one level to get the skinnerbox package root directory
project_directory = os.path.dirname(os.path.dirname(current_file_directory))

settings_path = os.path.join(project_directory, 'trial_config.json')
# Use os.path.join for consistent path separators across platforms
log_directory = os.path.join(project_directory, 'logs')
temp_directory = os.path.join(project_directory, 'temp')
gpioMonitor_directory = os.path.join(project_directory, 'gpioMonitor.json')

if not os.path.exists(log_directory):
    os.makedirs(log_directory)