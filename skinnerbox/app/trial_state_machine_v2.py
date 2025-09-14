import json
import threading
from trial_logger import Trial_Logger, SubjectInfo, ExperimentInfo
from time import time
from skinnerbox.app.typeDefs import *

class Trial_State_Machine:
    def __init__(self):
        self.settings = {}
        self.subjectInfo = SubjectInfo()
        self.experimentInfo = ExperimentInfo()
        self.state = TrialState.Idle
        self.startTime = None
        self.lock = threading.Lock()
        self.currentIteration = 0
        self.interactions = []
        self.interactable = True
        self.lastSuccessfulInteractTime = None
        self.lastStimulusTime = 0.0
        self.stimulusCooldownThread = None
        self.total_interactions = 0
        self.elapsed_time = 0
        self.endStatus = None
        self.logger = None
    
    def start_trial(self):
        if self.state != TrialState.Idle: return False
        
        # Load Settings
        try:
            with open('app/trial_config.json', 'r') as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            self.settings = {}

        goal = int(self.settings.get('goal', 0))
        duration = int(self.settings.get('duration', 0)) * 60

        self.timeRemaining = duration
        self.currentIteration = 0
        self.lastStimulusTime = time.time()

        self.state = TrialState.Running
        self.logger = Trial_Logger(self.subjectInfo, self.experimentInfo)

        threading.Thread(target=self.run_trial, args=(goal, duration)).start()
        self.give_stimulus()

        return True

    def stop_trial(self, reason):
        self.state = TrialState.Idle
        self.logger.log_event(self.get_time(), 1, f"Trial Stopped: {reason}")
        self.logger.stop()

    def get_time(self) -> float:
        return time.time - self.startTime

    def run_trial(self, goal, duration):
        """
        Runs the trial for the given duration or until the goal interactions are reached.
        """
        pass