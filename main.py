# skinnerBox.py
from datetime import datetime
import json
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("skinnerbox.main")

# Import app components
from app import app
from app import app_config
from app.trial_state_machine import TrialStateMachine
from app.app_config import log_directory

# Set up GPIO with error handling
try:
    from app.gpio import water_primer, start_trial_button, manual_interaction, start_motor, water
    gpio_available = True
    logger.info("GPIO components initialized successfully")
except Exception as e:
    gpio_available = False
    logger.warning(f"Error setting up GPIO components: {e}")
    logger.warning("Running in mock mode - GPIO functionality will be simulated")

trial_state_machine = None

#region Helper Functions
# Ensures log path exists
if not os.path.exists(log_directory):
    try:
        os.makedirs(log_directory)
        logger.info(f"Created log directory: {log_directory}")
    except Exception as e:
        logger.error(f"Failed to create log directory: {e}")

def list_log_files_sorted(log_directory):
    """
    List and sort log files by date
    """
    try:
        log_files = [f for f in os.listdir(log_directory) if f.startswith("log_") and f.endswith(".json")]
        return sorted(log_files, reverse=True)
    except Exception as e:
        logger.error(f"Error listing log files: {e}")
        return []

# Settings and File Management
def load_settings():
    """
    Load settings from configuration file with fallback to defaults
    """
    default_settings = {
        "duration": 15,
        "goal": 5,
        "cooldown": 5,
        "rewardType": "water",
        "stimulusType": "light",
        "light-color": "#00ff00"
    }
    
    try:
        if os.path.exists(app_config.settings_path):
            with open(app_config.settings_path, "r") as f:
                settings = json.load(f)
                logger.info("Settings loaded from file")
                return settings
        else:
            logger.warning(f"Settings file not found at {app_config.settings_path}, using defaults")
            save_settings(default_settings)
            return default_settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}, using defaults")
        return default_settings

def save_settings(settings):
    """
    Save settings to configuration file
    """
    try:
        with open(app_config.settings_path, "w") as f:
            json.dump(settings, f, indent=4)
            logger.info("Settings saved to file")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False
#endregion

# Run the app
if __name__ == '__main__':
    # Create a state machine
    trial_state_machine = TrialStateMachine()
    
    # Set up GPIO handlers if available
    if gpio_available:
        water_primer.when_pressed = start_motor  # Start the motor when the water primer is pressed
        start_trial_button.when_pressed = trial_state_machine.start_trial  # Start the trial when the start button is pressed
        manual_interaction.when_pressed = trial_state_machine.interact  # Register an interaction when the manual interaction button is pressed
    else:
        logger.info("GPIO handlers not set up (running in mock mode)")
    
    # Start the Flask app
    app.run(debug=False, use_reloader=False, host='0.0.0.0')