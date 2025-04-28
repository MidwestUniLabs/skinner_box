from setuptools import setup, find_packages
import os

# Read version from version.txt
try:
    with open("version.txt", "r") as f:
        version = f.read().strip()
except FileNotFoundError:
    raise RuntimeError("version.txt file is missing. Please ensure it exists in the project directory.")

# Read requirements from requirements.txt
try:
    with open("requirements.txt", "r") as f:
        requirements = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    raise RuntimeError("requirements.txt file is missing. Please ensure it exists in the project directory.")

# Read long description
try:
    with open("README.md", "r") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Source Code for the Skinner Box by Midwest UniLabs"

setup(
    name="Skinnerbox-Source",
    version=version,
    description="Source Code for the Skinner Box by Midwest UniLabs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="JDykman",
    author_email="jake@midwestunilabs.com",
    url="https://github.com/JDykman/skinner_box",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    package_data={
        "": ["version.txt", "requirements.txt", "README.md"],
        "app": ["*.py", "*.json", "templates/*.html", "static/css/*.css", "static/js/*.js"],
    },
    data_files=[
        ("", ["version.txt", "requirements.txt", "README.md"]),
    ],
    py_modules=["main", "skinnerbox_cli", "update_checker"],
    entry_points={
        "console_scripts": [
            "skinnerbox=skinnerbox_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)