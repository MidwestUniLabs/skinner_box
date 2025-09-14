# app/app_config.py
import os

# Get the absolute path of the current file's directory (e.g., /path/to/project/app)
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# Navigate up one level to get the project root directory (e.g., /path/to/project)
project_directory = os.path.dirname(current_file_directory)

# Use os.path.join for consistent path separators across platforms
settings_path = os.path.join(project_directory, 'trial_config.json')
log_directory = os.path.join(project_directory, 'logs/')
temp_directory = os.path.join(project_directory, 'temp/')
gpioMonitor_path = os.path.join(project_directory, 'gpioMonitor.json')

# Ensure required directories exist
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

if not os.path.exists(temp_directory):
    os.makedirs(temp_directory)