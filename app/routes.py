# app/routes.py
import csv
import os
from flask import render_template, request, jsonify, redirect, send_file, send_from_directory, url_for
import requests
from app import app, config, gpio
from app.trial_state_machine import TrialStateMachine
from main import list_log_files_sorted, load_settings, save_settings
from werkzeug.utils import secure_filename, safe_join
from openpyxl import Workbook
from app import gpio
import json

settings_path = config.settings_path
log_directory = config.log_directory
temp_directory = config.temp_directory
trial_state_machine = TrialStateMachine()

# Cloud Run URL
CLOUD_RUN_URL = os.getenv('CLOUD_RUN_URL')
TOKEN_FILE = "auth_token.json"

#region Helpers
def save_token(data):
    """
    Save the token to a file for persistence.
    """
    with open(TOKEN_FILE, "w") as file:
        json.dump(data, file)

def load_uname():
    """
    Load the token from the file if it exists.
    """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return json.load(file.username)
    return None

def load_email():
    """
    Load the token from the file if it exists.
    """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return json.load(file.email)
    return None

def load_token():
    """
    Load the token from the file if it exists.
    """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return json.load(file)
    return None

def delete_token():
    """
    Delete the token file to log out the user.
    """
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
#endregion

#region Routes
@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/testingpage')
def io_testing():
    return render_template('testingpage.html')

@app.route('/test_io', methods=['POST'])
def test_io():
    action = request.form.get('action')
    print(f"Button clicked: {action}")
    #TODO Add code to handle each action.
    if action == 'feed':
        gpio.feed()
    if action == 'water':
        gpio.water()
    if action == 'light':
        gpio.flashLightStim((255, 255, 255)) #TODO Change to settings color
    if action == 'sound':
        gpio.play_sound(1)
    if action == 'lever_press':
        gpio.lever_press()
        #TODO Put log interaction - manual
    if action == 'nose_poke':
        gpio.nose_poke()
        #TODO Put log interaction - manual

    return redirect(url_for('io_testing'))

@app.route("/pin_status")
def pin_status():
    # Collect the statuses of your GPIO components
    statuses = gpio.gpio_states
    # Return the statuses as a JSON response
    return jsonify(statuses)

@app.route('/trial', methods=['POST'])
def trial():
    settings = load_settings()  # Load settings
    if(trial_state_machine.state == 'running'):
        return render_template('runningtrialpage.html', settings=settings) #TODO change to trialpage
    else:
        settings = load_settings()  # Load settings
        # Perform operations based on settings...
        return render_template('trialsettingspage.html', settings=settings) #TODO change to trialsettings

@app.route('/start', methods=['POST'])
def start():
    global trial_state_machine
    settings = load_settings()  # Load settings
    if trial_state_machine.state == 'Running':
        return render_template('runningtrialpage.html', settings=settings)
    elif trial_state_machine.state == 'Idle':
        if trial_state_machine.start_trial():
            return render_template('runningtrialpage.html', settings=settings)
    elif trial_state_machine.state == 'Completed':
        trial_state_machine = TrialStateMachine()
        if trial_state_machine.start_trial():
            return render_template('runningtrialpage.html', settings=settings)
        return render_template('trialsettingspage.html', settings=settings)

@app.route('/stop', methods=['POST'])
def stop(): # Stops the trial
    if trial_state_machine.stop_trial():
        return redirect(url_for('trial_settings'))
    return redirect(url_for('trial_settings'))

@app.route('/trial-settings', methods=['GET'])
def trial_settings(): # Displays the trial settings with the settings loaded from the file
    settings = load_settings()
    return render_template('trialsettingspage.html', settings=settings)

@app.route('/update-trial-settings', methods=['POST'])
def update_trial_settings(): # Updates the trial settings with the form data
    settings = load_settings()
    for key in request.form:
        settings[key] = request.form[key]
    save_settings(settings)
    return redirect(url_for('trial_settings'))

@app.route('/trial-status')
def trial_status(): # Returns the current status of the trial
    global trial_state_machine
    try:
        # This returns the real-time values of countdown and current iteration
        trial_status = {
            'timeRemaining': trial_state_machine.timeRemaining,
            'currentIteration': trial_state_machine.currentIteration
        }
        print (trial_state_machine.timeRemaining)
        return jsonify(trial_status)
    except:
        return

@app.route('/log-viewer', methods=['GET', 'POST'])
def log_viewer(): # Displays the log files in the log directory
    log_files = list_log_files_sorted(log_directory)  # Get sorted list of log files
    return render_template('logpage.html', log_files=log_files)

@app.route('/download-raw-log/<filename>')
def download_raw_log_file(filename): # Download the raw log file
    filename = secure_filename(filename)  # Sanitize the filename
    try:
        return send_from_directory(directory=log_directory, path=filename, as_attachment=True, download_name=filename)
    except FileNotFoundError:
        return "Log file not found.", 404

@app.route('/download-excel-log/<filename>')
def download_excel_log_file(filename): # Download the Excel log file
    # Use safe_join to ensure the filename is secure
    secure_filename = safe_join(log_directory, filename)
    try:
        # Initialize a workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        if not os.path.exists(temp_directory):
            os.makedirs(temp_directory)
        
        # Define your column titles here
        column_titles = ['Date/Time', 'Total Time', 'Total Interactions', '', 'Entry', 'Interaction Time', 'Type', 'Reward', 'Interactions Between', 'Time Between']
        ws.append(column_titles)
        # Check if the file exists and is a CSV file
        if not os.path.isfile(secure_filename) or not filename.endswith('.csv'):
            print(f'CSV file not found or incorrect file type: {secure_filename}')
            return "Log file not found.", 404
        # Read the CSV file and append rows to the worksheet
        with open(secure_filename, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip the header of the CSV if it's already included
            for row in reader:
                ws.append(row)
        
        # Save the workbook to a temporary file
        temp_filename = f'{filename.rsplit(".", 1)[0]}.xlsx'
        temp_filepath = os.path.join(temp_directory, temp_filename)
        wb.save(temp_filepath)
        
        # Send the Excel file as an attachment
        return send_file(temp_filepath, as_attachment=True, download_name=temp_filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except FileNotFoundError:
        print(f'Excel file not found: {temp_filename}')
        return "Converted log file not found.", 404
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred while processing the request.", 500

@app.route('/view-log/<filename>')
def view_log(filename): # View the log file in the browser
    filename = secure_filename(filename)
    file_path = os.path.join(log_directory, filename)

    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            log_content = file.readlines()

        # Create an HTML table with the log content
        rows = []
        for line in log_content:
            cells = line.strip().split(',')
            rows.append(cells)
            
        # Pass the rows to the template instead of directly returning HTML
        return render_template("t_logviewer.html", rows=rows)
    else:
        return "Log file not found.", 404

@app.route('/login_user', methods=['POST'])
def Login_User():
    data = request.get_json()
    username = "test" # TODO
    email = data.get('email')
    password = data.get('password')
    """
    Log in the user and save the JWT token for future use.
    """
    try:
        response = requests.post(
            f'{CLOUD_RUN_URL}/login',
            json={'email': email, 'password': password},
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        token_data = response.json().get("data", {})
        if "access_token" in token_data:
            token_data["username"] = username
            token_data["email"] = email
            save_token(token_data)  # Save the token to a file
            print(f"Successfully logged in as {email}")
            return token_data
        else:
            print("Login succeeded, but no token received.")
            return {"error": "Login succeeded, but no token received."}, 400
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return {"error": str(http_err)}, 400
    except Exception as e:
        print(f"Error logging in: {e}")
        return {"error": str(e)}, 500

@app.route('/current_user', methods=['GET'])
def current_user():
    token_data = load_token()
    if token_data and "access_token" in token_data:
        return {"current_user": token_data.get("username")}
    return {"current_user": None}
#endregion

#region External API Calls
@app.route('/logout_user', methods=['POST'])
def logout_user():
    """
    Log out the user by deleting their token.
    """
    try:
        delete_token()  # Deletes the auth_token.json file
        print("User logged out successfully.")
        return {"message": "User logged out successfully."}, 200
    except Exception as e:
        print(f"Error logging out user: {e}")
        return {"error": "Failed to log out user."}, 500

def Push_Data(data):
    # Push data to Cloud Run
    try:
        response = requests.post(f'{CLOUD_RUN_URL}/data/push', json=data)
        response.raise_for_status()
        print(f'Pushing data to Cloud Run: {CLOUD_RUN_URL}')
        return True
    except Exception as e:
        print(f'Error pushing data to Cloud Run: {e}')
        return False

def Pull_User_Logs(username): #TODO This should only be accessible when the user is logged in and should get the username from that
    # Pull user logs from Cloud Run
    try:
        response = requests.get(f'{CLOUD_RUN_URL}/logs/user', params={'name': username})
        response.raise_for_status()
        print(f'Pulling user logs from Cloud Run: {CLOUD_RUN_URL}')
        return response.json()
    except Exception as e:
        print(f'Error pulling user logs from Cloud Run: {e}')
        return False
    
def Pull_User_Data(username) :#TODO This should only be accessible when the user is logged in and should get the username from that
    # Pull user data from Cloud Run
    try:
        response = requests.get(f'{CLOUD_RUN_URL}/users/get', params={'name': username})
        response.raise_for_status()
        print(f'Pulling user data from Cloud Run: {CLOUD_RUN_URL}')
        return response.json()
    except Exception as e:
        print(f'Error pulling user data from Cloud Run: {e}')
        return False

def Get_Protected_Data():
    """
    Fetch data from a protected endpoint using the stored JWT token.
    """
    token_data = load_token()
    if not token_data or "access_token" not in token_data:
        print("No valid token found. Please log in first.")
        return None

    access_token = token_data["access_token"]
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f'{CLOUD_RUN_URL}/protected', headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return None
    except Exception as e:
        print(f"Error fetching protected data: {e}")
        return None
#endregion
