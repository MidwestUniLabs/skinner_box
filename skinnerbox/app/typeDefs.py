from enum import Enum
from dataclasses import dataclass
from __future__ import annotations

class TrialState(Enum):
    Idle = "Idle"
    Running = "Running"

class EventType(Enum):
    Reward : RewardTypes
    Interaction: InteractionTypes
    Stimulus: StimulusTypes

class RewardTypes(Enum):
    Water = "Water"
    Food = "Food"

class InteractionTypes(Enum):
    LeverPress = "LeverPress"
    NosePoke = "NosePoke"

class StimulusTypes(Enum):
    Auditory = "Auditory"
    Visual = "Visual"
    NoneStim = "None"

@dataclass
class SubjectInfo:
    SubjectID: int
    Species_And_Strain: str
    Sex: str
    Date_Of_Birth: str
    Body_Weight_Pre_Session: float
    Body_Weight_Post_Session: float
    Deprivation_Level: str

@dataclass
class ExperimentInfo:
    Experiment_ID: str
    Researcher_Name: str
    Experimental_Group: str
    Session_Number: int
    RewardType: RewardTypes
    InteractionType: InteractionTypes
    StimulusType: StimulusTypes

@dataclass
class EnviromentInfo:
    Box_ID: str
    Session_Date: str
    Session_Start_Time: str
    Session_End_Time: str
    Notes: str

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
            SubjectID=int(self.settings.get('SubjectID', 0)),
            Species_And_Strain=self.settings.get('Species_And_Strain', 'N/A'),
            Sex=self.settings.get('Sex', 'Unknown'),
            Date_Of_Birth=self.settings.get('Date_Of_Birth', 'Unknown'),
            Body_Weight_Pre_Session=float(self.settings.get('Body_Weight_Pre_Session', 0.0)),
            Body_Weight_Post_Session=float(self.settings.get('Body_Weight_Post_Session', 0.0)),
            Deprivation_Level=self.settings.get('Deprivation_Level', 'N/A')
        )

    def build_experiment_info(self) -> ExperimentInfo:
        """Constructs the ExperimentInfo object."""
        return ExperimentInfo(
            Experiment_ID=self.settings.get('Experiment_ID', 'Default-Experiment'),
            Researcher_Name=self.settings.get('Researcher_Name', 'N/A'),
            Experimental_Group=self.settings.get('Experimental_Group', 'Control'),
            Session_Number=int(self.settings.get('Session_Number', 1)),
            RewardType=RewardTypes(self.settings.get('RewardType', 'Food')),
            InteractionType=InteractionTypes(self.settings.get('InteractionType', 'LeverPress')),
            StimulusType=StimulusTypes(self.settings.get('StimulusType', 'None'))
        )

    def build_enviroment_info(self) -> EnviromentInfo:
        """Constructs the EnviromentInfo object."""
        # For a more robust solution, you could use the datetime module
        # to generate timestamps automatically if they aren't in settings.
        return EnviromentInfo(
            Box_ID=self.settings.get('Box_ID', 'Box-1'),
            Session_Date=self.settings.get('Session_Date', 'N/A'),
            Session_Start_Time=self.settings.get('Session_Start_Time', 'N/A'),
            Session_End_Time=self.settings.get('Session_End_Time', ''),
            Notes=self.settings.get('Notes', '')
        )