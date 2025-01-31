# app/routes.py
import csv
import os
from flask import render_template, request, jsonify, redirect, send_file, send_from_directory, url_for
import requests
from app import app, app_config, gpio
from app.trial_state_machine import TrialStateMachine
from main import list_log_files_sorted, load_settings, save_settings, trial_state_machine
from werkzeug.utils import secure_filename, safe_join
from openpyxl import Workbook
from app import gpio
import json
from functools import wraps
from flask import abort
import app.trial_state_machine as statemachine  # Import the state machine

settings_path = app_config.settings_path
log_directory = app_config.log_directory
temp_directory = app_config.temp_directory
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_data = load_token()
        if not token_data or "access_token" not in token_data:
            print("Access denied. User not logged in.")
            return abort(401)  # Unauthorized
        return f(*args, **kwargs)
    return decorated_function
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
    data = request.get_json()  # Ensure correct JSON request handling
    if not data or "action" not in data:
        return jsonify({"error": "Missing action parameter"}), 400

    action = data["action"]
    print(f"Button clicked: {action}")

    try:
        if action == 'feeder':
            gpio.feed()
            return jsonify({"message": "Feeder activated"}), 200

        elif action == 'water':
            gpio.water()
            return jsonify({"message": "Water dispensed"}), 200

        elif action == 'light':
            color = (255, 255, 255)  # Default to white if settings are not available
            try:
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    color = tuple(settings.get("light_color", [255, 255, 255]))
            except Exception as e:
                print(f"Error reading settings: {e}")

            gpio.flashLightStim(color)
            return jsonify({"message": "Light stimulus activated", "color": color}), 200

        elif action == 'sound':
            gpio.play_sound(1)
            return jsonify({"message": "Sound stimulus activated"}), 200

        elif action == 'lever':
            gpio.lever_press(trial_state_machine)
            if hasattr(statemachine, "log_manual_interaction"):
                statemachine.log_manual_interaction("lever_press")  # Correctly calls state machine log
            return jsonify({"message": "Lever press logged"}), 200

        elif action == 'poke':
            gpio.nose_poke()
            if hasattr(statemachine, "log_manual_interaction"):
                statemachine.log_manual_interaction("nose_poke")  # Correctly calls state machine log
            return jsonify({"message": "Nose poke logged"}), 200

        else:
            return jsonify({"error": "Invalid action"}), 400

    except Exception as e:
        print(f"Error processing action {action}: {e}")
        return jsonify({"error": f"Failed to execute {action}"}), 500
    
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
    if trial_state_machine.finish_trial():
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

@app.route('/download-raw-log/<filename>') #TODO Update to accept json (if needed)
def download_raw_log_file(filename): # Download the raw log file
    filename = secure_filename(filename)  # Sanitize the filename
    try:
        return send_from_directory(directory=log_directory, path=filename, as_attachment=True, download_name=filename)
    except FileNotFoundError:
        return "Log file not found.", 404

@app.route('/download-excel-log/<filename>') #TODO Update to accept json
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

@app.route('/view-log/<filename>') # TODO Deprecate
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
def login_user():
    data = request.get_json()
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
        if "access_token" in token_data and "username" in token_data:
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

@app.route('/push_data', methods=['POST'])
@login_required
def push_data():
    # Get the user token data
    token_data = load_token()
    username = token_data.get("username")
    if not username:
        return {"error": "Username not found in token."}, 400

    # Get the trial log file from the request
    if 'file' not in request.files:
        return {"error": "No file part in the request."}, 400
    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file."}, 400

    # Secure the filename and save it temporarily
    filename = secure_filename(file.filename)
    temp_filepath = os.path.join(temp_directory, filename)
    file.save(temp_filepath)

    # Prepare the data to be sent
    data = {
        'username': username,
        'box_id': request.form.get('box_id'),
        'trial_log': open(temp_filepath, 'r').read()
    }

    # Push data to Cloud Run
    try:
        response = requests.post(f'{CLOUD_RUN_URL}/data/push', json=data)
        response.raise_for_status()
        print(f'Pushing data to Cloud Run: {CLOUD_RUN_URL}')
        return {"message": "Data pushed successfully."}, 200
    except Exception as e:
        print(f'Error pushing data to Cloud Run: {e}')
        return {"error": str(e)}, 500
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@app.route('/pull_user_logs', methods=['GET'])
@login_required
def pull_user_logs():
    """
    Fetch logs for the current user from Cloud Run.
    """
    token_data = load_token()
    username = token_data.get("username")
    if not username:
        return {"error": "Username not found in token."}, 400

    # Token for authorization
    YOUR_ACCESS_TOKEN = token_data.get("access_token")
    headers = {'Authorization': f"Bearer {YOUR_ACCESS_TOKEN}"}

    try:
        url = f'{CLOUD_RUN_URL}/trials/get'
        params = {'name': username}

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors (e.g., 404, 401)

        # Process trials from the response
        processed_trials = []
        for trial in response.json().get("data", []):
            trialInfo = {
                "id": trial.get("id"),
                "pi_id": trial.get("pi_id"),
                "start_time": trial.get("start_time"),
                "end_time": trial.get("end_time"),
                "status": trial.get("status"),
                "total_interactions": trial.get("total_interactions"),
                "valuesInfoPosition": []  # Initialize for trial entries
            }

            for entry in trial.get("trial_entries", []):
                entryInfo = {
                    "entry_num": entry.get("entry_num"),
                    "rel_time": entry.get("rel_time"),
                    "type": entry.get("type"),
                    "reward": entry.get("reward"),
                    "interactions_between": entry.get("interactions_between"),
                    "time_between": entry.get("time_between"),
                }
                trialInfo["valuesInfoPosition"].append(entryInfo)

            processed_trials.append(trialInfo)

        return {"data": processed_trials, "success": True}

    except requests.exceptions.RequestException as req_err:
        print(f"Request error pulling user logs from Cloud Run: {req_err}")
        return {"error": "Failed to connect to the logs service.", "details": str(req_err)}, 500
    except Exception as e:
        print(f"Error processing user logs: {e}")
        return {"error": str(e)}, 500


# def Pull_User_Data(username) :#TODO This should only be accessible when the user is logged in and should get the username from that
#     # Pull user data from Cloud Run
#     try:
#         response = requests.get(f'{CLOUD_RUN_URL}/users/get', params={'name': username})
#         response.raise_for_status()
#         print(f'Pulling user data from Cloud Run: {CLOUD_RUN_URL}')
#         return response.json()
#     except Exception as e:
#         print(f'Error pulling user data from Cloud Run: {e}')
#         return False

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
