import json
import threading
import asyncio
import os
from datetime import datetime
from skinnerbox.app.trial_logger import TrialLogger, SubjectInfo, ExperimentInfo
from time import time
from skinnerbox.app.type_defs import *
from skinnerbox.app import gpio

class TrialStateMachine:
    def __init__(self):
        self.settings = {}
        self.subject_info = SubjectInfo(subject_id=0, species_and_strain="", sex="", date_of_birth="", body_weight_post_session=0, body_weight_pre_session=0, deprivation_level="")
        self.experiment_info = ExperimentInfo(experiment_id="", researcher_name="", experimental_group="", session_number=0, reward_type=RewardTypes.FOOD, interaction_type=InteractionTypes.LEVER_PRESS, stimulus_type=StimulusTypes.NONE_STIM)
        self.state = TrialState.IDLE
        self.start_time = None
        self.lock = threading.Lock()
        self.current_iteration = 0
        self.interactions = []
        self.interactable = True
        self.last_successful_interact_time = None
        self.last_stimulus_time = 0.0
        self.stimulus_cooldown_thread = None
        self.total_interactions = 0
        self.elapsed_time = 0
        self.end_status = None
        self.logger = None
        self.trial_completed_log_file = None
        self.loop = None
        self.logger_thread = None

    def start_trial(self):
        if self.state != TrialState.IDLE: return False
        
        # Load Settings
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'trial_config.json')
            with open(config_path, 'r') as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            self.settings = {}

        goal = int(self.settings.get('goal', 0))
        duration = int(self.settings.get('duration', 0)) * 60
        
        info_builder = InfoBuilder(self.settings)
        self.subject_info = info_builder.build_subject_info()
        self.experiment_info = info_builder.build_experiment_info()

        self.time_remaining = duration
        self.current_iteration = 0
        self.last_stimulus_time = time()

        self.state = TrialState.RUNNING
        
        safe_time_str = datetime.now().strftime("%m_%d_%y_%H_%M_%S").replace(":", "_")
        log_filename = f"log_{safe_time_str}.json"
        
        self.logger = TrialLogger(log_filename, self.subject_info, self.experiment_info)
        
        # Run the logger in a separate thread with its own event loop
        self.logger_thread = threading.Thread(target=self.run_logger, daemon=True)
        self.logger_thread.start()
        
        # Wait a bit for logger to start
        threading.Event().wait(0.1)

        threading.Thread(target=self.run_trial, args=(goal, duration)).start()
        self.give_stimulus()

        return True

    def run_logger(self):
        """Run the logger with its own event loop in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.logger.start())
        # Keep the loop running for log_event calls
        self.loop.run_forever()

    def stop_trial(self, reason):
        self.state = TrialState.IDLE
        if self.loop and self.logger:
            # Set final status for JSON output
            self.logger.set_status(reason)
            asyncio.run_coroutine_threadsafe(
                self.logger.log_event(self.get_time(), EventType.REWARD_GIVEN, f"Trial Stopped: {reason}"),
                self.loop
            )
            asyncio.run_coroutine_threadsafe(self.logger.stop(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)

    def get_time(self) -> float:
        if self.start_time is None:
            return 0.0
        return time() - self.start_time

    def run_trial(self, goal, duration):
        """
        Runs the trial for the given duration or until the goal interactions are reached.
        """
        self.start_time = time()
        interaction_type = self.settings.get('interactionType')
        if interaction_type == 'lever':
            gpio.lever.when_pressed = self.lever_press
        elif interaction_type == 'poke':
            gpio.poke.when_pressed = self.nose_poke

        while self.state == TrialState.RUNNING:
            self.elapsed_time = self.get_time()
            self.time_remaining = max(0, round(duration - self.elapsed_time, 2))
            
            cooldown_time = float(self.settings.get('cooldown', 0))
            if self.interactable and (time() - self.last_stimulus_time) >= cooldown_time:
                self.give_stimulus()
                self.last_stimulus_time = time()
            
            allow_overtime = self.settings.get('allowOvertime') == 'on'

            if goal > 0 and self.current_iteration >= goal:  # Goal reached
                self.finish_trial(end_status="Goal Reached")
                break

            if not allow_overtime and duration > 0 and self.time_remaining <= 0:  # Time limit reached and no overtime
                self.finish_trial(end_status="Time Limit Reached")
                break
            
            threading.Event().wait(0.1)

    def finish_trial(self, end_status):
        with self.lock:
            if self.state == TrialState.RUNNING:
                self.state = TrialState.COMPLETED
                self.end_status = end_status
                self.trial_completed_log_file = self.logger.filename
                if self.loop and self.logger:
                    # Set final status for JSON output
                    self.logger.set_status(end_status)
                    asyncio.run_coroutine_threadsafe(
                        self.logger.log_event(self.get_time(), EventType.REWARD_GIVEN, f"Trial Finished: {end_status}"),
                        self.loop
                    )
                    asyncio.run_coroutine_threadsafe(self.logger.stop(), self.loop)
                    self.loop.call_soon_threadsafe(self.loop.stop)
                return True
            return False

    def lever_press(self):
        current_time = self.get_time()
        self.total_interactions += 1

        if self.state == TrialState.RUNNING and self.interactable:
            if self.last_successful_interact_time is not None:
                time_between = (current_time - self.last_successful_interact_time).__round__(2)
            else:
                time_between = 0

            self.interactable = False
            self.current_iteration += 1
            self.give_reward()
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(current_time, EventType.INTERACTION_RECIEVED, "Lever Press (Correct)"),
                    self.loop
                )
            self.last_successful_interact_time = current_time
        else:
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(current_time, EventType.INTERACTION_RECIEVED, "Lever Press (Incorrect)"),
                    self.loop
                )

    def nose_poke(self):
        current_time = self.get_time()
        self.total_interactions += 1

        if self.state == TrialState.RUNNING and self.interactable:
            if self.last_successful_interact_time is not None:
                time_between = (current_time - self.last_successful_interact_time).__round__(2)
            else:
                time_between = 0

            self.interactable = False
            self.current_iteration += 1
            self.give_reward()
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(current_time, EventType.INTERACTION_RECIEVED, "Nose Poke (Correct)"),
                    self.loop
                )
            self.last_successful_interact_time = current_time
        else:
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(current_time, EventType.INTERACTION_RECIEVED, "Nose Poke (Incorrect)"),
                    self.loop
                )

    def give_stimulus(self):
        stimulus_type = self.settings.get('stimulusType')
        if stimulus_type == 'light':
            hex_color = self.settings.get('light-color')
            gpio.flash_light_stim(hex_color)
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(self.get_time(), EventType.STIMULUS_GIVEN, "Light Stimulus"),
                    self.loop
                )
        elif stimulus_type == 'tone':
            # TODO: Play sound
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(self.get_time(), EventType.STIMULUS_GIVEN, "Tone Stimulus"),
                    self.loop
                )
        
        self.interactable = True
        self.last_stimulus_time = time()

    def give_reward(self):
        reward_type = self.settings.get('rewardType')
        if reward_type == 'water':
            gpio.water()
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(self.get_time(), EventType.REWARD_GIVEN, "Water"),
                    self.loop
                )
        elif reward_type == 'food':
            gpio.feed()
            if self.loop and self.logger:
                asyncio.run_coroutine_threadsafe(
                    self.logger.log_event(self.get_time(), EventType.REWARD_GIVEN, "Food"),
                    self.loop
                )
        
        cooldown = float(self.settings.get('cooldown', 0))
        threading.Timer(cooldown, self.give_stimulus).start()
