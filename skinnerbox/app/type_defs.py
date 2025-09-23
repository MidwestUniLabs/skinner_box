from __future__ import annotations

from enum import Enum
from dataclasses import dataclass


class TrialState(Enum):
    IDLE = "Idle"
    RUNNING = "Running"
    COMPLETED = "Completed"

class EventType(Enum):
    REWARD_GIVEN = "RewardGiven"
    INTERACTION_RECIEVED = "InteractionReceived"
    STIMULUS_GIVEN = "StimulusGiven"

class RewardTypes(Enum):
    WATER = "Water"
    FOOD = "Food"

class InteractionTypes(Enum):
    LEVER_PRESS = "LeverPress"
    NOSE_POKE = "NosePoke"

class StimulusTypes(Enum):
    AUDITORY = "Auditory"
    VISUAL = "Visual"
    NONE_STIM = "None"

@dataclass
class SubjectInfo:
    subject_id: int
    species_and_strain: str
    sex: str
    date_of_birth: str
    body_weight_pre_session: float
    body_weight_post_session: float
    deprivation_level: str

@dataclass
class ExperimentInfo:
    experiment_id: str
    researcher_name: str
    experimental_group: str
    session_number: int
    reward_type: RewardTypes
    interaction_type: InteractionTypes
    stimulus_type: StimulusTypes

@dataclass
class EnviromentInfo:
    box_id: str
    session_date: str
    session_start_time: str
    session_end_time: str
    notes: str

@dataclass
class LogEntry:
    """A dataclass to hold a single, structured log event."""
    timestamp: float
    event: EventType
    data: str

class InfoBuilder:
    """
    Builds the various Info dataclasses from a settings dictionary.
    """
    def __init__(self, settings: dict):
        self.settings = settings

    def build_subject_info(self) -> SubjectInfo:
        """Constructs the SubjectInfo object."""
        return SubjectInfo(
            subject_id=int(self.settings.get('SubjectID', 0)),
            species_and_strain=self.settings.get('Species_And_Strain', 'N/A'),
            sex=self.settings.get('Sex', 'Unknown'),
            date_of_birth=self.settings.get('Date_Of_Birth', 'Unknown'),
            body_weight_pre_session=float(self.settings.get('Body_Weight_Pre_Session', 0.0)),
            body_weight_post_session=float(self.settings.get('Body_Weight_Post_Session', 0.0)),
            deprivation_level=self.settings.get('Deprivation_Level', 'N/A')
        )

    def build_experiment_info(self) -> ExperimentInfo:
        """Constructs the ExperimentInfo object."""
        # Map config values to enum values
        reward_map = {'water': RewardTypes.WATER, 'food': RewardTypes.FOOD}
        interaction_map = {'lever': InteractionTypes.LEVER_PRESS, 'poke': InteractionTypes.NOSE_POKE}
        stimulus_map = {'light': StimulusTypes.VISUAL, 'tone': StimulusTypes.AUDITORY, 'none': StimulusTypes.NONE_STIM}
        
        reward_type = reward_map.get(self.settings.get('rewardType', 'food').lower(), RewardTypes.FOOD)
        interaction_type = interaction_map.get(self.settings.get('interactionType', 'lever').lower(), InteractionTypes.LEVER_PRESS)
        stimulus_type = stimulus_map.get(self.settings.get('stimulusType', 'none').lower(), StimulusTypes.NONE_STIM)
        
        return ExperimentInfo(
            experiment_id=self.settings.get('Experiment_ID', 'Default-Experiment'),
            researcher_name=self.settings.get('Researcher_Name', 'N/A'),
            experimental_group=self.settings.get('Experimental_Group', 'Control'),
            session_number=int(self.settings.get('Session_Number', 1)),
            reward_type=reward_type,
            interaction_type=interaction_type,
            stimulus_type=stimulus_type
        )

    def build_enviroment_info(self) -> EnviromentInfo:
        """Constructs the EnviromentInfo object."""
        # For a more robust solution, you could use the datetime module
        # to generate timestamps automatically if they aren't in settings.
        return EnviromentInfo(
            box_id=self.settings.get('Box_ID', 'Box-1'),
            session_date=self.settings.get('Session_Date', 'N/A'),
            session_start_time=self.settings.get('Session_Start_Time', 'N/A'),
            session_end_time=self.settings.get('Session_End_Time', ''),
            notes=self.settings.get('Notes', '')
        )