#!/usr/bin/env python3
"""
Skinner Box CLI launcher script.
This provides a command-line entry point when the package is installed.
"""
import sys
import os
import logging
import traceback
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("skinnerbox.cli")

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description='Run Skinner Box application')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    
    args = parser.parse_args()
    
    # Add the current directory to the path so we can import the app
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    try:
        logger.info("Starting Skinner Box application...")
        
        # Import the necessary modules
        try:
            from main import trial_state_machine
        except ImportError:
            logger.warning("Failed to import trial_state_machine from main, trying direct import")
            from app.trial_state_machine import TrialStateMachine
            trial_state_machine = TrialStateMachine()
        
        # Import the Flask app
        try:
            from app import app
        except ImportError:
            logger.error("Failed to import Flask app")
            print("Error: Could not import the Flask app. Please ensure all dependencies are installed.")
            return 1
        
        # Print startup message
        print("=" * 60)
        print(" Skinner Box Application ".center(60, "="))
        print("=" * 60)
        print(f"Server running on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the Flask app
        app.run(debug=args.debug, use_reloader=False, host=args.host, port=args.port)
        return 0
    
    except ImportError as e:
        print(f"Error starting application: {e}")
        print("Please make sure all dependencies are installed.")
        logger.error(f"Import error: {e}")
        return 1
    
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        return 0
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())