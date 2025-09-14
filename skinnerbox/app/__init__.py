# app/__init__.py
import os
from flask import Flask

app = Flask(__name__, template_folder='../templates', static_folder='../static')
try:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version.txt'), 'r') as f:
        __version__ = f.read().strip()
except FileNotFoundError:
    __version__ = "0.0.0"
    
from skinnerbox.app import routes