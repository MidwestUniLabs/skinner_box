import asyncio
import aiofiles
from skinnerbox.app.typeDefs import *

class Trial_Logger:
    """
    Logs trial data asynchronously using an asyncio.Queue and a writer task.
    """
    def __init__(self, filename: str, subject_info: SubjectInfo, experiment_info: ExperimentInfo):
        self.filename = filename
        self.subject_info = subject_info
        self.experiment_info = experiment_info
        self.queue = asyncio.Queue()
        self.writer_task = None # To hold background task

    async def _write_header(self):
        """Asynchronously writes the header to the file."""
        async with aiofiles.open(self.filename, 'w', newline='') as f:
            # aiofiles doesn't have a direct csv writer, so we format strings
            await f.write(f'# Subject ID:,{self.subject_info.SubjectID}\n')
            await f.write(f'# Species:,{self.subject_info.Species_And_Strain}\n')
            await f.write(f'# Experimenter:,{self.experiment_info.Researcher_Name}\n')
            await f.write(f'# Session_Number:,{self.experiment_info.Session_Number}\n')
            await f.write(f'# Reward Type:,{self.experiment_info.RewardType}\n')
            await f.write(f'# Interaction Type:,{self.experiment_info.InteractionType}\n')
            await f.write(f'# Stimulus Type:,{self.experiment_info.StimulusType}\n')
            await f.write('\n')
            await f.write('Timestamp,Event,Data\n')

    async def _writer_loop(self):
        """The consumer task that pulls from the queue and writes to disk."""
        # Open the file once and keep it open for the duration of the loop
        async with aiofiles.open(self.filename, 'a', newline='') as f:
            while True:
                # Wait for an item to appear in the queue
                entry = await self.queue.get()
                
                # A 'None' entry is the signal to stop
                if entry is None:
                    self.queue.task_done()
                    break
                
                # Write the entry to the file
                await f.write(f'{entry.timestamp},{entry.event},{entry.data}\n')
                
                # Signal that the task is done
                self.queue.task_done()

    async def log_event(self, timestamp: float, event: EventType, data: str):
        """The producer method: quickly adds a log entry to the queue."""
        entry = LogEntry(timestamp, event, data)
        await self.queue.put(entry)
    
    async def start(self):
        """Starts the logger by writing the header and creating the writer task."""
        print("Starting logger...")
        await self._write_header()
        self.writer_task = asyncio.create_task(self._writer_loop())
        print("Logger started. Background writer is running.")

    async def stop(self):
        """Gracefully stops the logger."""
        print("Stopping logger...")
        # Add a sentinel value (None) to the queue to signal the writer to exit
        await self.queue.put(None)
        # Wait for the queue to be fully processed
        await self.queue.join()
        # Wait for the writer task to finish completely
        await self.writer_task
        print("Logger stopped.")