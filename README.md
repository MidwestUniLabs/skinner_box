# Skinner Box

This repository contains the code for running and managing a Skinner Box experimental setup.

## Table of Contents

- [First Time Setup](#first-time-setup)
- [Installation with setup.py](#installation-with-setuppy)
- [Running the Application](#running-the-application)
- [Development and Versioning](#development-and-versioning)
- [Network Configuration](#network-configuration)
- [Automating with Crontab](#automating-with-crontab)
- [Running in WSL](#running-in-wsl)
- [Troubleshooting](#troubleshooting)

## First Time Setup

### On Raspberry Pi:

1. Download and unzip the repository on your Raspberry Pi
2. Navigate to the project directory and run the installer script:
   ```
   $ chmod +x installer.sh
   $ ./installer.sh
   ```
   This will install all necessary packages and dependencies.

3. After installation, verify that all components are working properly:
   ```
   $ python test.py
   ```

## Installation with setup.py

For development installations or if the installer script doesn't meet your needs, you can use setup.py:

1. Install in development mode (changes to code take effect immediately):
   ```
   $ pip install -e .
   ```

2. Install as a regular package:
   ```
   $ pip install .
   ```

3. Build a distribution package:
   ```
   $ python setup.py sdist bdist_wheel
   ```
   This creates distributable packages in the `dist/` directory.

4. Install specific dependencies:
   ```
   $ pip install -r requirements.txt
   ```

Note: The setup.py file automatically reads the version from "version.txt" and requirements from "requirements.txt".

## Running the Application

You can run the application using either the shell script or directly with Python:

```
$ ./run.sh
```

Or:

```
$ python run.py
```

## Development and Versioning

### Version Control:

When merging changes with the main branch, use bump2version to increment version numbers:

```
$ bump2version [major|minor|patch]
```

Examples:
- For major version changes: `bump2version major`
- For minor feature additions: `bump2version minor`
- For bug fixes: `bump2version patch`

### Contributing:

1. Create a feature branch from main
2. Make your changes
3. Run tests to ensure functionality
4. Submit a pull request

## Network Configuration

To set up the network on Raspberry Pi:

1. Click on the network icon in the top right corner of the screen
2. Select "Advanced Connections" → "Edit Connections" → "Wired Connection 1" → "Settings" → "IPv4 Settings"
3. Change "Method" to "Manual"
4. Click "Add" under "Additional Static Addresses"
5. Open a terminal and type `ifconfig` to get your network information
6. In the Network Connection dialog:
   - Address: Enter the inet address shown in the terminal (or your preferred custom value)
   - Netmask: Enter the netmask value from terminal
   - Gateway: Enter the broadcast address from terminal
7. Click "Save" to apply changes
8. Restart the network service:
   ```
   $ sudo service networking restart
   ```

## Automating with Crontab

To set up automatic execution:

1. Open a terminal and enter:
   ```
   $ crontab -e
   ```

2. Select your preferred editor if prompted

3. Add one of the following lines at the end of the file:
   
   - To run the script daily at 8 AM:
     ```
     0 8 * * * cd /path/to/skinner_box && ./run.sh > /path/to/skinner_box/logs/daily_run.log 2>&1
     ```

   - To run on system startup:
     ```
     @reboot cd /path/to/skinner_box && ./run.sh > /path/to/skinner_box/logs/startup.log 2>&1
     ```

4. Save and exit the editor

## Running in WSL

To run this application in a Debian WSL virtual environment:

1. Navigate to the project directory:
   ```
   $ cd /mnt/c/Users/jacob/Documents/GitHub/skinner_box
   ```

2. Create a virtual environment if you haven't already:
   ```
   $ python -m venv venv
   ```

3. Activate the virtual environment:
   ```
   $ source venv/bin/activate
   ```

4. Install required dependencies:
   ```
   $ pip install -r requirements.txt
   ```
   (If requirements.txt doesn't exist, create it or install dependencies manually)

5. Run the application:
   ```
   $ python main.py
   ```

### Additional Dependencies for WSL

You might need to install additional packages depending on your setup:
- For GPIO functionality (if running on a Raspberry Pi): `pip install RPi.GPIO gpiozero`
- For the Flask web app: `pip install flask`

## Troubleshooting

### Common Issues:

1. **GPIO Permission Errors**: If you encounter permission issues when accessing GPIO pins, try:
   ```
   $ sudo chmod -R 777 /dev/gpiomem
   ```

2. **Network Connection Issues**: Verify your network settings with:
   ```
   $ ping 8.8.8.8
   ```

3. **Application Not Starting**: Check the logs in the `logs/` directory

For additional help, please create an issue on the GitHub repository.

