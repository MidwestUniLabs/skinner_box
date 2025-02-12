# app/state_machine.py
import threading
import json
import os
import time
from app import gpio
from dotenv import load_dotenv
from app.app_config import log_directory

class TrialStateMachine: #TODO Clean up the code
    """
    A state machine to manage the trial process in a behavioral experiment.
    Attributes:
        state (str): The current state of the trial.
        lock (threading.Lock): A lock to ensure thread safety.
        currentIteration (int): The current iteration of the trial.
        settings (dict): The settings loaded from a configuration file.
        startTime (float): The start time of the trial.
        interactable (bool): Whether the system is currently interactable.
        lastSuccessfulInteractTime (float): The time of the last successful interaction.
        lastStimulusTime (float): The time of the last stimulus.
        stimulusCooldownThread (threading.Timer): The thread handling stimulus cooldown.
        log_path (str): The path to the log file.
        interactions_between (int): The number of interactions between successful interactions.
        time_between (float): The time between successful interactions.
        total_interactions (int): The total number of interactions.
        total_time (float): The total time of the trial.
        interactions (list): A list of interactions during the trial.
    Methods:
        load_settings(): Loads settings from a configuration file.
        start_trial(): Starts the trial.
        pause_trial(): Pauses the trial.
        resume_trial(): Resumes the trial.
        stop_trial(): Stops the trial.
        run_trial(goal, duration): Runs the trial logic.
        lever_press(): Handles a lever press interaction.
        nose_poke(): Handles a nose poke interaction.
        queue_stimulus(): Queues a stimulus after a cooldown period.
        give_stimulus(): Gives a stimulus immediately.
        light_stimulus(): Handles the light stimulus.
        noise_stimulus(): Handles the noise stimulus.
        give_reward(): Gives a reward based on the settings.
        add_interaction(interaction_type, reward_given, interactions_between=0, time_between=''): Logs an interaction.
        push_log(): Writes the log to a file.
        finish_trial(): Finishes the trial and logs the results.
        error(): Handles errors and sets the state to 'Error'.
        pause_trial_logic(): Logic to pause the trial.
        resume_trial_logic(): Logic to resume the trial.
        handle_error(): Logic to handle errors.
    """
    def __init__(self):
        self.state = 'Idle'
        self.lock = threading.Lock()
        self.currentIteration = 0
        self.settings = {}
        self.startTime = None
        self.interactable = True
        self.lastSuccessfulInteractTime = None
        self.lastStimulusTime = 0.0
        self.stimulusCooldownThread = None
        self.log_path = log_directory
        self.interactions_between = 0
        self.time_between = 0.0
        self.total_interactions = 0
        self.elapsed_time = 0
        self.endStatus = None
        self.interactions = []

    def load_settings(self):
        # Implementation of loading settings from file
        try:
            with open('app/trial_config.json', 'r') as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            self.settings = {}
            
    def start_trial(self):
        with self.lock:
            if self.state == 'Idle':
                self.load_settings()
                goal = int(self.settings.get('goal', 0))
                duration = int(self.settings.get('duration', 0)) * 60
                self.timeRemaining = duration
                self.currentIteration = 0
                self.lastStimulusTime = time.time()
                self.state = 'Running'
                # Format the current time to include date and time in the filename
                # YYYY_MM_DD_HH_MM_SS
                safe_time_str = time.strftime("%m_%d_%y_%H_%M_%S").replace(":", "_")
                # Update log_path to include the date and time
                self.log_path = log_directory + f"log_{safe_time_str}.json"
                threading.Thread(target=self.run_trial, args=(goal, duration)).start()
                self.give_stimulus()
                return True
            return False

    def pause_trial(self):
        with self.lock:
            if self.state == 'Running':
                self.state = 'Paused'
                self.pause_trial_logic()
                return True
            return False

    def resume_trial(self):
        with self.lock:
            if self.state == 'Paused':
                self.state = 'Running'
                self.resume_trial_logic()
                return True
            return False

    def stop_trial(self):
        with self.lock:
            if self.state in ['Preparing', 'Running', 'Paused']:
                self.state = 'Idle'
                return True
            return False

    def run_trial(self, goal, duration):
        """
        Runs the trial for the given duration or until the goal interactions are reached.
        """
        self.startTime = time.time()
        self.currentIteration = 0  # Ensure iteration count starts at zero

        # Assign interaction callbacks
        interaction_type = self.settings.get('interactionType')
        if interaction_type == 'lever':
            gpio.lever.when_pressed = self.lever_press
        elif interaction_type == 'poke':
            gpio.poke.when_pressed = self.nose_poke

        while self.state == 'Running':
            # Ensure `timeRemaining` updates correctly
            self.elapsed_time = time.time() - self.startTime
            self.timeRemaining = max(0, round(duration - self.elapsed_time, 2))

            # Re-stimulate if no interaction has occurred within the cooldown time
            cooldown_time = float(self.settings.get('cooldown', 0))
            if self.interactable and (self.elapsed_time - self.lastStimulusTime) >= cooldown_time:
                print("No interaction in last cooldown period, Re-Stimming")
                self.give_stimulus()
                self.lastStimulusTime = self.elapsed_time  # Update stimulus time

            # **Check if trial should finish**
            if self.currentIteration >= goal: # Goal reached
                self.elapsed_time = round(self.elapsed_time, 2)

                self.finish_trial(endStatus="Goal Reached")
                break

            elif self.timeRemaining <= 0: # Time limit reached
                self.elapsed_time = round(self.elapsed_time, 2)
                self.finish_trial(endStatus="Time Limit Reached")
                break

            time.sleep(0.1)  # Small sleep interval to reduce CPU usage

    ## Interactions ##
    def lever_press(self):
        current_time = time.time()
        self.total_interactions += 1

        if self.state == 'Running' and self.interactable:
            # Calculate time between only if the last interaction was when interactable was True
            if self.lastSuccessfulInteractTime is not None:
                self.time_between = (current_time - self.lastSuccessfulInteractTime).__round__(2)
            else:
                self.time_between = 0  # Default for the first successful interaction

            self.interactable = False  # Disallow further interactions until reset
            self.currentIteration += 1
            self.give_reward()
            self.add_interaction("Lever", True, self.interactions_between, self.time_between)
            self.lastSuccessfulInteractTime = current_time  # Update only on successful interaction when interactable
            self.interactions_between = 0
        else:
            self.add_interaction("Lever", False, self.interactions_between, 0)
            self.interactions_between += 1

    def nose_poke(self):
        current_time = time.time()
        self.total_interactions += 1

        if self.state == 'Running' and self.interactable:
            if self.lastSuccessfulInteractTime is not None:
                self.time_between = (current_time - self.lastSuccessfulInteractTime).__round__(2)
            else:
                self.time_between = 0  # Default for the first successful interaction

            self.interactable = False
            self.currentIteration += 1
            self.give_reward()
            self.add_interaction("Poke", True, self.interactions_between, self.time_between)
            self.lastSuccessfulInteractTime = current_time  # Update only on successful interaction when interactable
            self.interactions_between = 0
        else:
            self.add_interaction("Poke", False, self.interactions_between, 0)
            self.interactions_between += 1

    ## Stimulus' ##
    def queue_stimulus(self): # Give after cooldown
        if(self.settings.get('stimulusType') == 'light' and self.interactable == False):
            self.stimulusCooldownThread = threading.Timer(float(self.settings.get('cooldown', 0)), self.light_stimulus)
            self.stimulusCooldownThread.start()
        elif(self.settings.get('stimulusType') == 'tone' and self.interactable == False):
            self.stimulusCooldownThread = threading.Timer(float(self.settings.get('cooldown', 0)), self.noise_stimulus)
            self.stimulusCooldownThread.start()

    def give_stimulus(self): #Give immediately
        if(self.settings.get('stimulusType') == 'light'):
            self.light_stimulus()
        elif(self.settings.get('stimulusType') == 'tone'):
            self.noise_stimulus()
        self.lastStimulusTime = time.time()  # Reset the timer after delivering the stimulus

    def light_stimulus(self):
        hex_color = self.settings.get('light-color')  # Html uses hexadecimal colors
        gpio.flashLightStim(hex_color)
        self.interactable = True
        self.lastStimulusTime = time.time()

    def noise_stimulus(self):
        if(self.interactable == False):
            #TODO Make noise
            self.interactable = True

    ## Reward ##
    def give_reward(self):
        if(self.settings.get('rewardType') == 'water'):
            gpio.water()
        elif(self.settings.get('rewardType') == 'food'):
            gpio.feed()
        self.queue_stimulus()

    ## Logging ##
    def add_interaction(self, interaction_type, reward_given, interactions_between=0, time_between=''):
        entry = self.total_interactions
        interaction_time = (time.time() - self.startTime).__round__(2)
        
        # Log the interaction
        self.interactions.append([entry, interaction_time, interaction_type, reward_given, interactions_between, time_between])
    
    def log_manual_interaction(action_type):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "interaction": action_type
        }

        log_file = "manual_interactions.json"
        try:
            with open(log_file, "a") as f:
                json.dump(log_entry, f)
                f.write("\n")
            print(f"Logged manual interaction: {action_type}")
        except Exception as e:
            print(f"Error logging interaction: {e}")
            
    def push_log(self):
        """
        Converts trial logs to JSON format and writes them to a file.
        """
        load_dotenv()
        pi_id = os.getenv("PI_ID")

        log_data = {
            "pi_id": pi_id,
            "status": self.endStatus,
            "start_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.startTime)),
            "end_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.startTime + self.elapsed_time)),
            "total_interactions": self.total_interactions,
            "trial_entries": [
                {
                    "entry_num": entry[0],
                    "rel_time": entry[1],
                    "type": entry[2],
                    "reward": entry[3],
                    "interactions_between": entry[4],
                    "time_between": entry[5]
                }
                for entry in self.interactions
            ]
        }

        # Ensure log directory exists
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_filename = f"{self.log_path}"
        with open(log_filename, 'w') as file:
            json.dump(log_data, file, indent=4)

        print(f"Log saved: {log_filename}")

    def finish_trial(self, endStatus):
        with self.lock:
            if self.state == 'Running':
                self.state = 'Completed'
                self.endStatus = endStatus
                self.push_log()
                print("Trial complete")
                return True
            return False

    def error(self):
        with self.lock:
            self.state = 'Error'
            self.handle_error()
            self.state = 'Idle'

    def pause_trial_logic(self):
        """
        Pauses the trial by disabling interactions.
        """
        self.interactable = False  # Prevent new interactions
        self.state = 'Paused'
        print("Trial Paused")

    def resume_trial_logic(self):
        """
        Resumes the trial by enabling interactions.
        """
        self.interactable = True  # Allow new interactions
        self.state = 'Running'
        print("Trial Resumed")

    def handle_error(self, error_message="An unknown error occurred"):
        """
        Handles errors by logging and changing state.
        """
        self.state = 'Error'
        print(f"Error: {error_message}")
        self.push_log()

