# app/__init__.py
from flask import Flask

app = Flask(__name__, template_folder='../templates', static_folder='../static')
__version__ = "0.4.10"

from skinnerbox.app import routes