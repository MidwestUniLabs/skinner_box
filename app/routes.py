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

@app.route('/manuallyEndTrial', methods=['POST'])
def manuallyEndTrial(): # Stops the trial
    if trial_state_machine.finish_trial("Manually Ended"):
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
def download_excel_log_file(filename):
    """
    Convert a JSON log file into an Excel file and provide it for download.
    """
    filename = secure_filename(filename)
    file_path = os.path.join(log_directory, filename)

    if not os.path.isfile(file_path):
        return jsonify({"error": "Log file not found."}), 404

    try:
        # Load JSON log data
        with open(file_path, 'r') as file:
            trial_data = json.load(file)

        # Create an Excel workbook and sheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Trial Log"

        # Add trial summary
        summary_headers = ["Pi ID", "Status", "Start Time", "End Time", "Total Interactions"]
        ws.append(summary_headers)
        ws.append([
            trial_data.get("pi_id", "N/A"),
            trial_data.get("status", "N/A"),
            trial_data.get("start_time", "N/A"),
            trial_data.get("end_time", "N/A"),
            trial_data.get("total_interactions", "N/A"),
        ])

        # Add spacing row
        ws.append([])

        # Add trial entry details
        entry_headers = ["Entry #", "Relative Time", "Type", "Reward", "Interactions Between", "Time Between"]
        ws.append(entry_headers)

        for entry in trial_data.get("trial_entries", []):
            ws.append([
                entry.get("entry_num", "N/A"),
                entry.get("rel_time", "N/A"),
                entry.get("type", "N/A"),
                "Yes" if entry.get("reward", False) else "No",
                entry.get("interactions_between", "N/A"),
                entry.get("time_between", "N/A"),
            ])

        # Save the workbook to a temporary file
        temp_filename = f'{filename.rsplit(".", 1)[0]}.xlsx'
        temp_filepath = os.path.join(temp_directory, temp_filename)
        wb.save(temp_filepath)

        # Send the Excel file as an attachment
        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=temp_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        app.logger.error(f"Error converting log to Excel: {e}")
        return jsonify({"error": "An error occurred while processing the request."}), 500

@app.route('/view-log/<filename>')
def view_log(filename):
    """
    Fetches and returns the contents of a local log file as JSON.
    """
    filename = secure_filename(filename)
    file_path = os.path.join(log_directory, filename)

    if not os.path.isfile(file_path):
        print(f"Log file not found: {file_path}")
        return jsonify({"error": "Log file not found."}), 404

    try:
        with open(file_path, 'r') as file:
            trial_data = json.load(file)  # Assuming logs are JSON formatted

        return jsonify(trial_data)

    except Exception as e:
        print(f"Error reading log file: {e}")
        return jsonify({"error": "Error loading log content."}), 500


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

@app.route('/push_log', methods=['POST'])
@login_required
def push_log():
    """
    Read a JSON trial log file, push it to the API, and delete it locally upon success.
    """
    token_data = load_token()
    if not token_data or "username" not in token_data:
        return jsonify({"error": "Invalid authentication token."}), 403

    # Ensure file is uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    # Secure filename and save temporarily
    filename = secure_filename(file.filename)
    temp_filepath = os.path.join(temp_directory, filename)
    file.save(temp_filepath)

    try:
        # Read JSON log file
        with open(temp_filepath, 'r') as log_file:
            trial_data = json.load(log_file)

        # Ensure required fields exist
        required_fields = ["pi_id", "status", "start_time", "end_time", "total_interactions", "trial_entries"]
        if not all(field in trial_data for field in required_fields):
            return jsonify({"error": "Invalid log format. Missing required fields."}), 400

        # Validate trial entries
        for entry in trial_data["trial_entries"]:
            required_entry_fields = ["entry_num", "rel_time", "type", "reward", "interactions_between", "time_between"]
            if not all(field in entry for field in required_entry_fields):
                return jsonify({"error": "Invalid entry format. Missing required fields."}), 400

        # Attach UID to ensure the trial is linked to the user
        trial_data["uid"] = token_data.get("uid")

        # Send request to Cloud Run API
        headers = {'Authorization': f"Bearer {token_data.get('access_token')}"}
        response = requests.post(f'{CLOUD_RUN_URL}/trials/push', json=trial_data, headers=headers)

        # Handle response
        if response.status_code in [200, 201]:
            local_log_path = os.path.join(log_directory, filename)
            if os.path.exists(local_log_path):
                os.remove(local_log_path)
                print(f"Deleted local log after push: {local_log_path}")
            return jsonify({"message": "Log pushed successfully and deleted locally.", "response": response.json()}), response.status_code
        else:
            return jsonify({"error": "Failed to push log to API", "api_response": response.text}), response.status_code


    except Exception as e:
        app.logger.error(f'Error processing log file: {e}')
        return jsonify({"error": "An error occurred while processing the log."}), 500

    finally:
        # Clean up temporary file
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

@app.route('/list_local_logs', methods=['GET'])
def list_local_logs():
    """
    List all local log files in the log directory.
    """
    try:
        log_files = [f for f in os.listdir(log_directory) if os.path.isfile(os.path.join(log_directory, f))]
        return jsonify({"log_files": log_files}), 200
    except Exception as e:
        print(f"Error listing local logs: {e}")
        return jsonify({"error": "Failed to list local logs."}), 500

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
