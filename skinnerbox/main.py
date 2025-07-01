import os

# Environment management
class EnvironmentManager:
    """Manages environment configuration and setup."""
    
    # Constants
    DEVELOPMENT_ENVIRONMENT_NAME = 'development'
    PRODUCTION_ENVIRONMENT_NAME = 'production'
    DEFAULT_HOST_DEV = '127.0.0.1'
    DEFAULT_HOST_PROD = '0.0.0.0'
    DEFAULT_PORT = 5000

    def __init__(self):
        self._setup_dotenv()
        self._load_environment_file()

    def _setup_dotenv(self):
        """Setup dotenv with proper error handling."""
        try:
            from dotenv import load_dotenv
            self.load_dotenv = load_dotenv
            print("python-dotenv available")
        except ImportError:
            print("python-dotenv not installed, using system environment variables only")
            self.load_dotenv = lambda *args: None

    def _load_environment_file(self):
        """Load environment-specific .env file."""
        # First check if ENVIRONMENT is already set
        env_name = os.environ.get('ENVIRONMENT', self.DEVELOPMENT_ENVIRONMENT_NAME)
        env_file = f'.env.{env_name}'
        
        try:
            if os.path.exists(env_file):
                self.load_dotenv(env_file, override=False)
                print(f"Loaded environment from {env_file}")
            elif os.path.exists('.env'):
                self.load_dotenv('.env', override=False)
                print("Loaded default .env file")
            else:
                print("No .env file found, using system environment variables only")
        except Exception as e:
            print(f"Could not load .env file: {e}")

    def get_config(self):
        """Get environment configuration from environment variables with sensible defaults."""
        environment = os.environ.get('ENVIRONMENT', self.DEVELOPMENT_ENVIRONMENT_NAME)
        debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
        default_host = self.DEFAULT_HOST_DEV if environment == self.DEVELOPMENT_ENVIRONMENT_NAME else self.DEFAULT_HOST_PROD
        host = os.environ.get('HOST', default_host)
        port = int(os.environ.get('PORT', str(self.DEFAULT_PORT)))
        
        # Debug print to verify configuration
        print(f"Environment Config:")
        print(f"  ENVIRONMENT: {environment}")
        print(f"  DEBUG: {debug_mode}")
        print(f"  HOST: {host}")
        print(f"  PORT: {port}")

        return environment, debug_mode, host, port

    def is_production(self, environment):
        """Check if current environment is production."""
        return environment == self.PRODUCTION_ENVIRONMENT_NAME

    def is_development(self, environment):
        """Check if current environment is development."""
        return environment == self.DEVELOPMENT_ENVIRONMENT_NAME


# GPIO and Hardware Setup
def setup_gpio_components(environment_manager, environment):
    """Setup GPIO components for production environment."""
    if environment_manager.is_production(environment):
        try:
            from skinnerbox.app.gpio import water_primer, start_trial_button, manual_interaction, start_motor, water
            print("GPIO components imported successfully")
            return water_primer, start_trial_button, manual_interaction, start_motor, water
        except ImportError as e:
            print(f"Error setting up GPIO components: {e}")
            return None, None, None, None, None
    else:
        print("Development mode - GPIO disabled")
        return None, None, None, None, None


def setup_gpio_handlers(environment_manager, environment, gpio_components, trial_state_machine):
    """Configure GPIO event handlers for production environment."""
    water_primer, start_trial_button, manual_interaction, start_motor, water = gpio_components
    
    if environment_manager.is_production(environment) and water_primer is not None:
        try:
            water_primer.when_pressed = start_motor
            start_trial_button.when_pressed = trial_state_machine.start_trial
            manual_interaction.when_pressed = water
            print("GPIO event handlers configured successfully")
        except Exception as e:
            print(f"GPIO setup failed - continuing without hardware buttons: {e}")
    elif environment_manager.is_development(environment):
        print("Development mode - GPIO handlers not configured")


# Application Setup
def ensure_log_directory():
    """Create log directory if it doesn't exist."""
    try:
        from skinnerbox.app.app_config import log_directory
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
            print(f"Created log directory: {log_directory}")
        else:
            print(f"Log directory exists: {log_directory}")
    except ImportError as e:
        print(f"Could not import log_directory config: {e}")


def display_network_info(environment_manager, environment):
    """Display network information in production environment."""
    if environment_manager.is_production(environment):
        print("Production environment - displaying network info:")
        os.system('hostname -I')
    else:
        print("Development environment - network info not displayed")


def initialize_application(environment_manager):
    """Initialize the application components and return configuration."""
    try:
        from skinnerbox.app import app
        from skinnerbox.app.trial_state_machine import TrialStateMachine
    except ImportError as e:
        print(f"Error importing application components: {e}")
        raise

    environment, debug_mode, host, port = environment_manager.get_config()
    gpio_components = setup_gpio_components(environment_manager, environment)
    ensure_log_directory()
    
    trial_state_machine = TrialStateMachine()
    setup_gpio_handlers(environment_manager, environment, gpio_components, trial_state_machine)

    return app, environment, debug_mode, host, port


# Main Application
def main():
    """Main function to run the application."""
    try:
        environment_manager = EnvironmentManager()
        app, environment, debug_mode, host, port = initialize_application(environment_manager)
        display_network_info(environment_manager, environment)

        print(f"Starting Flask app in {environment} mode on {host}:{port}")
        print(f"Debug mode: {debug_mode}")
        
        app.run(debug=debug_mode, use_reloader=debug_mode, host=host, port=port)
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        raise


if __name__ == '__main__':
    main()