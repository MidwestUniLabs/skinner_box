from flask import Flask, render_template, jsonify, request
import os
import logging

logger = logging.getLogger("skinnerbox.flask_app")

# Initialize the Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))

# Flask routes will be defined here
@app.route('/')
def index():
    return render_template('index.html')

# Add API routes as needed
@app.route('/api/status')
def status():
    return jsonify({"status": "running"})