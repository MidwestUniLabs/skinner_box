# app/__init__.py

"""
Flask application initialization and configuration
"""
import os
import sys
import logging
from flask import Flask
import importlib.resources as pkg_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("skinnerbox.app")

def create_app():
    """Create and configure the Flask application"""
    # Determine the template and static folder paths
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    template_folder = os.path.join(package_root, 'templates')
    static_folder = os.path.join(package_root, 'static')
    
    # Check if directories exist
    if not os.path.exists(template_folder):
        logger.warning(f"Template folder not found at {template_folder}, using default")
        template_folder = None
        
    if not os.path.exists(static_folder):
        logger.warning(f"Static folder not found at {static_folder}, using default")
        static_folder = None
    
    logger.info(f"Using template folder: {template_folder}")
    logger.info(f"Using static folder: {static_folder}")
    
    # Create the Flask app
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
                
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'development_key')
    
    # Log configuration
    logger.info(f"Flask app created with template folder: {app.template_folder}")
    logger.info(f"Flask app created with static folder: {app.static_folder}")
    
    return app

# Create the application instance
app = create_app()

# Import routes after app is created to avoid circular imports
import app.routes