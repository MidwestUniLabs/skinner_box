import os
from flask import render_template, request, jsonify, redirect, send_file, send_from_directory, url_for
import requests
from skinnerbox.app import app_config, gpio, app
from skinnerbox.app.trial_state_machine import TrialStateMachine
from skinnerbox.utils import list_log_files_sorted, load_settings, save_settings
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from skinnerbox.app import gpio
import json
from functools import wraps
from flask import abort, make_response
import skinnerbox.app.trial_state_machine as statemachine
from cryptography.fernet import Fernet
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize the limiter without passing 'app' directly
limiter = Limiter(key_func=get_remote_address)

# Later in your app setup
limiter.init_app(app)

settings_path = app_config.settings_path
log_directory = app_config.log_directory
temp_directory = app_config.temp_directory
trial_state_machine = TrialStateMachine()

# Cloud Run URL
CLOUD_RUN_URL = os.getenv('CLOUD_RUN_URL')

# Secure token and key file paths
FERNET_KEY_FILE = "fernet_key.secure"
TOKEN_FILE = "token.secure"

#region Helpers
def get_or_create_fernet_key():
    """
    Retrieve an existing FERNET_KEY from the environment or a file.
    If none exists, create and securely store a new one.
    """
    # 1. Try loading from environment variable
    env_key = os.getenv("FERNET_KEY")
    if env_key:
        return env_key.encode()

    # 2. Try loading from local file
    if os.path.exists(FERNET_KEY_FILE):
        with open(FERNET_KEY_FILE, "rb") as key_file:
            return key_file.read().strip()  # remove extra whitespace

    # 3. If no key exists, generate a new one and save it
    new_key = Fernet.generate_key()
    with open(FERNET_KEY_FILE, "wb") as key_file:
        key_file.write(new_key)
    print("🔑 New FERNET_KEY generated and saved securely.")
    return new_key
#endregion

#region Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_data = load_token("access_token")
        if not token_data:
            print("Access denied. User not logged in.")
            return abort(401)
        return f(*args, **kwargs)
    return decorated_function

def reauth_if_needed(func):
    """
    Decorator to refresh the access token if it has expired.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        token_data = load_token("access_token")  # Load stored tokens
        refresh_token = load_token("refresh_token")
        if not token_data:
            return jsonify({"error": "Unauthorized - No access token found."}), 401

        # Test the token by making a simple request
        headers = {"Authorization": f"Bearer {token_data}"}
        test_response = requests.get(f"{CLOUD_RUN_URL}/test-auth", headers=headers)

        if test_response.status_code == 401:  # Token expired, attempt refresh
            print("Access token expired. Attempting reauthentication...")

            if not refresh_token:
                print("No refresh token available. User must log in again.")
                return jsonify({"error": "No refresh token found. Please log in again."}), 401

            # Send refresh token in Authorization header
            reauth_response = requests.post(
                f"{CLOUD_RUN_URL}/refresh",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {refresh_token}"  # ✅ Send refresh token in header
                }
            )

            if reauth_response.status_code == 200:
                new_token_data = reauth_response.json().get("data", {})

                if "access_token" in new_token_data:
                    token_data = new_token_data["access_token"]
                    save_token(token_data)  # ✅ Update stored token
                    print("Reauthenticated successfully.")

                    # ✅ Retry the original function now that we have a fresh token
                    return func(*args, **kwargs)
                else:
                    print("Reauthentication failed: No new token received.")
                    return jsonify({"error": "Reauthentication failed."}), 401
            else:
                print("Reauthentication request failed.")
                return jsonify({"error": "Reauthentication request failed."}), 401

        return func(*args, **kwargs)  # ✅ Proceed with the original request if no reauth needed

    return wrapper
#endregion

#region Token Management
def save_token(data):
    """
    Encrypt and securely store token data in TOKEN_FILE.
    Ideally, data should be a dictionary (e.g. {"access_token": "..."}).
    """
    app.config["FERNET_KEY"] = get_or_create_fernet_key()
    cipher = Fernet(app.config["FERNET_KEY"])

    # Convert data to JSON string, then encrypt
    json_payload = json.dumps(data)
    encrypted_data = cipher.encrypt(json_payload.encode())

    # Overwrites file by default
    with open(TOKEN_FILE, "wb") as file:
        file.write(encrypted_data)

def delete_token():
    """Delete the token file to log out the user."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def load_token(field=None):
    """
    Load and decrypt stored authentication token from TOKEN_FILE.
    If field is given, return only token_data[field].
    Otherwise, return the entire dictionary or string.
    """
    if not os.path.exists(TOKEN_FILE):
        print("❌ Token file does not exist.")
        return None

    # Load the Fernet key
    app.config["FERNET_KEY"] = get_or_create_fernet_key()
    try:
        cipher = Fernet(app.config["FERNET_KEY"])
    except Exception as e:
        print(f"❌ Invalid FERNET_KEY: {e}")
        return None

    # Read and decrypt the file contents
    try:
        with open(TOKEN_FILE, "rb") as file:
            encrypted_data = file.read()
        decrypted_data = cipher.decrypt(encrypted_data)
    except Exception as e:
        print(f"❌ Error reading or decrypting token file: {e}")
        return None

    # Attempt to parse JSON
    try:
        token_data = json.loads(decrypted_data.decode())
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
        return None

    # token_data could be a dict or a string, depending on how it was originally saved
    if isinstance(token_data, dict):
        return token_data.get(field) if field else token_data
    else:
        # The data is not a dictionary (maybe just a string), so return it directly.
        # (If you strictly want a dict, you can raise an error here instead.)
        return token_data
#endregion

#region Home Page
@app.route('/')
def homepage():
    return render_template('homepage.html')
#endregion Home Page

#region Testing Page
@app.route('/testingpage')
def io_testing():
    return render_template('testingpage.html')

@app.route('/test_io', methods=['POST'])
def test_io():
    data = request.get_json()
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
                statemachine.log_manual_interaction("lever_press")
            return jsonify({"message": "Lever press logged"}), 200

        elif action == 'poke':
            gpio.nose_poke()
            if hasattr(statemachine, "log_manual_interaction"):
                statemachine.log_manual_interaction("nose_poke")
            return jsonify({"message": "Nose poke logged"}), 200

        else:
            return jsonify({"error": "Invalid action"}), 400

    except Exception as e:
        print(f"Error processing action {action}: {e}")
        return jsonify({"error": f"Failed to execute {action}"}), 500
#endregion Testing Page

#region Trial Page
@app.route('/trial', methods=['POST'])
def trial():
    settings = load_settings()  # Load settings
    if(trial_state_machine.state == 'running'):
        return render_template('trialpage.html', settings=settings) #TODO change to trialpage
    else:
        settings = load_settings()  # Load settings
        # Perform operations based on settings...
        return render_template('trialsettingspage.html', settings=settings) #TODO change to trialsettings

@app.route('/manuallyEndTrial', methods=['POST'])
def manuallyEndTrial(): # Stops the trial
    if trial_state_machine.finish_trial("Manually Ended"):
        return redirect(url_for('trial_settings'))
    return redirect(url_for('trial_settings'))
#endregion Trial Page

#region Trial Settings
@app.route('/trial-settings', methods=['GET'])
def trial_settings(): # Displays the trial settings with the settings loaded from the file
    settings = load_settings()
    return render_template('trialsettingspage.html', settings=settings)

@app.route('/update-trial-settings', methods=['POST'])
def update_trial_settings():
    # This part is perfect
    settings = load_settings()
    for key in request.form:
        settings[key] = request.form[key]
    save_settings(settings)

    # Instead of redirecting, return a JSON response
    return jsonify(success=True, message="Settings updated successfully.")

@app.route('/start', methods=['POST'])
def start():
    global trial_state_machine
    settings = load_settings()  # Load settings
    if trial_state_machine.state == 'Running':
        return render_template('trialpage.html', settings=settings)
    elif trial_state_machine.state == 'Idle':
        if trial_state_machine.start_trial():
            return render_template('trialpage.html', settings=settings)
    elif trial_state_machine.state == 'Completed':
        trial_state_machine = TrialStateMachine()
        if trial_state_machine.start_trial():
            return render_template('trialpage.html', settings=settings)
        return render_template('trialsettingspage.html', settings=settings)
#endregion Trial Settings

@app.route('/trial-status') #TODO Is this used?
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

#region Log Viewer Page
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

        #TODO The temp file is not being deleted
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

@app.route('/push_log', methods=['POST'])
@login_required
@reauth_if_needed
def push_log():
    """
    Read a JSON trial log file, push it to the API, and delete it locally upon success.
    """
    token_data = load_token("access_token")
    uid = load_token("username")
    if not token_data:
        return jsonify({"error": "Invalid authentication token."}), 403

    # Get the filename from the form data (no file upload required)
    filename = request.form.get('file')
    if not filename:
        return jsonify({"error": "No file selected."}), 400

    # Secure the filename and get its full path
    filename = secure_filename(filename)
    file_path = os.path.join(log_directory, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": f"File '{filename}' not found."}), 404

    try:
        # Read JSON log file
        with open(file_path, 'r') as log_file:
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

        # Attach UID to ensure the trial is linked to the correct user
        trial_data["uid"] = uid

        # Send the request to the Cloud Run API
        headers = {'Authorization': f"Bearer {token_data}"}
        response = requests.post(f'{CLOUD_RUN_URL}/trials/push', json=trial_data, headers=headers)

        # Handle response
        if response.status_code in [200, 201]:
            os.remove(file_path)  # Delete the file after successful push
            print(f"Deleted local log after push: {file_path}")
            return jsonify({"message": "Log pushed successfully and deleted locally.", "response": response.json()}), response.status_code
        else:
            app.logger.error(f"Failed to push log: {response.text}")
            return jsonify({"error": "Failed to push log to API", "api_response": response.text}), response.status_code

    except json.JSONDecodeError as e:
        app.logger.error(f'Error decoding JSON: {e}')
        return jsonify({"error": "Invalid JSON format in log file."}), 400
    except Exception as e:
        app.logger.error(f'Error processing log file: {e}')
        return jsonify({"error": "An unexpected error occurred while processing the log."}), 500


@app.route('/pull_user_logs', methods=['GET']) #TODO Sort by newest (by default)
@login_required
@reauth_if_needed
def pull_user_logs():
    """
    Fetch logs for the current user from Cloud Run.
    """
    username = load_token("username")
    if not username:
        return {"error": "Username not found in token."}, 400

    # Token for authorization
    YOUR_ACCESS_TOKEN = load_token("access_token")
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

@app.route('/list_local_logs', methods=['GET']) #TODO Sort by newest (by default)
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
#endregion Log Viewer Page

#region User Authentication
@app.route('/login_user', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 attempts per minute
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        response = requests.post(
            f'{CLOUD_RUN_URL}/login',
            json={'email': email, 'password': password},
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        token_data = response.json().get("data", {})

        if "access_token" in token_data and "refresh_token" in token_data:
            save_token(token_data)
            # Set HTTP-Only Secure Cookies
            resp = make_response({"message": "Login successful"})
            resp.set_cookie("access_token", token_data["access_token"], httponly=True, secure=True, samesite='Strict')
            resp.set_cookie("refresh_token", token_data["refresh_token"], httponly=True, secure=True, samesite='Strict')
            return resp

        return {"error": "Login failed"}, 400
    except requests.exceptions.HTTPError as http_err:
        return {"error": str(http_err)}, 400

@app.route('/current_user', methods=['GET'])
def current_user():
    token_data = load_token("username")
    if token_data:
        return {"current_user": token_data}
    return {"current_user": None}

@app.route('/reauth_user', methods=['POST'])
def reauth_user():
    """
    Refresh the user's access token using the stored refresh token.
    """
    refresh_token = load_token("refresh_token")
    if not refresh_token:
        return {"error": "No refresh token found."}, 400

    try:
        response = requests.post(
            f'{CLOUD_RUN_URL}/refresh',
            json={},
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {refresh_token}"
            }
        )
        response.raise_for_status()

        new_token_data = response.json().get("data", {})

        if "access_token" in new_token_data:
            token_data = load_token("access_token")  # Load stored token data
            token_data = new_token_data["access_token"]  # Update access token only
            save_token(token_data)  # Save updated token data
            print("Successfully refreshed token.")
            return new_token_data
        else:
            print("Token refresh succeeded, but no token received.")
            return {"error": "Token refresh succeeded, but no token received."}, 400

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return {"error": str(http_err)}, 400
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return {"error": str(e)}, 500

@app.route('/logout_user', methods=['POST'])
def logout_user():
    resp = make_response({"message": "User logged out successfully."})
    resp.set_cookie("access_token", "", expires=0)
    resp.set_cookie("refresh_token", "", expires=0)
    return resp



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