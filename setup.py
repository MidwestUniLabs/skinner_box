from setuptools import setup, find_packages

# Constants for file paths
VERSION_FILE = "version.txt"
REQUIREMENTS_FILE = "requirements.txt"
README_FILE = "README.md"

# Project metadata
PROJECT_NAME = "skinnerbox"
PROJECT_DESCRIPTION = "Source Code for the Skinner Box by Midwest UniLabs"
PROJECT_URL = "https://github.com/JDykman/skinner_box"
AUTHOR_NAME = "JDykman"
AUTHOR_EMAIL = "jake@midwestunilabs.com"
MIN_PYTHON_VERSION = ">=3.6"


def read_file_content(filename):
    """Helper function to read and return file content."""
    with open(filename, "r") as f:
        return f.read().strip()


def read_requirements(filename):
    """Helper function to read and parse requirements file."""
    with open(filename, "r") as f:
        return [line.strip() for line in f.readlines()
                if line.strip() and not line.startswith("#")]


# Read project version and requirements
version = read_file_content(VERSION_FILE)
requirements = read_requirements(REQUIREMENTS_FILE)
long_description = read_file_content(README_FILE)

# Package configuration
package_config = {
    "name": PROJECT_NAME,
    "version": version,
    "description": PROJECT_DESCRIPTION,
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": AUTHOR_NAME,
    "author_email": AUTHOR_EMAIL,
    "url": PROJECT_URL,
    "packages": find_packages(),
    "include_package_data": True,
    "install_requires": requirements,
    "entry_points": {
        'console_scripts': [
            f'{PROJECT_NAME}={PROJECT_NAME}:main',
        ],
    },
    "classifiers": [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    "python_requires": MIN_PYTHON_VERSION,
}

setup(**package_config)
