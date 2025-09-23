import asyncio
import aiofiles
import json
import os
from datetime import datetime
from skinnerbox.app.type_defs import *
from skinnerbox.app import app_config

class TrialLogger:
    """
    Logs trial data asynchronously using an asyncio.Queue and a writer task.
    """
    def __init__(self, filename: str, subject_info: SubjectInfo, experiment_info: ExperimentInfo):
        # Keep the base filename for UI routes; compute full path for saving
        self.filename = filename  # e.g., 'log_MM_DD_YY_HH_MM_SS.json'
        self.filepath = os.path.join(app_config.log_directory, filename)
        self.subject_info = subject_info
        self.experiment_info = experiment_info
        self.queue = asyncio.Queue()
        self.writer_task = None  # Background consumer task
        self.entries = []  # Accumulated trial entries for JSON output
        self.start_wall_clock = datetime.now()
        self.status = "Running"

    async def _write_header(self):
        """No-op placeholder maintained for compatibility."""
        return

    async def _writer_loop(self):
        """Consume log entries and accumulate them for final JSON write on stop."""
        while True:
            entry = await self.queue.get()
            if entry is None:
                self.queue.task_done()
                break

            # Map LogEntry -> viewer schema
            entry_num = len(self.entries) + 1
            event_type_name = entry.event.name if isinstance(entry.event, EventType) else str(entry.event)
            is_interaction = (event_type_name == "INTERACTION_RECIEVED")
            # Infer reward from data string containing "(Correct)"
            reward_given = isinstance(entry.data, str) and "Correct" in entry.data

            normalized = {
                "entry_num": entry_num,
                "rel_time": float(entry.timestamp) if entry.timestamp is not None else 0.0,
                "type": "Interaction" if is_interaction else str(entry.event),
                "reward": bool(reward_given),
                "interactions_between": 0,
                "time_between": 0.0,
            }
            self.entries.append(normalized)
            self.queue.task_done()

    async def log_event(self, timestamp: float, event: EventType, data: str):
        """The producer method: quickly adds a log entry to the queue."""
        entry = LogEntry(timestamp, event, data)
        await self.queue.put(entry)
    
    def set_status(self, status: str):
        """Set final status to be written to JSON (e.g., 'Goal Reached', 'Time Limit Reached', 'Manually Ended')."""
        self.status = status

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

        # Compose JSON structure and write once at the end
        end_wall_clock = datetime.now()
        trial_json = {
            "pi_id": str(self.subject_info.subject_id),
            "status": self.status,
            "start_time": self.start_wall_clock.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": end_wall_clock.strftime('%Y-%m-%d %H:%M:%S'),
            "total_interactions": sum(1 for e in self.entries if e.get("type") == "Interaction"),
            "trial_entries": self.entries,
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        async with aiofiles.open(self.filepath, 'w') as f:
            await f.write(json.dumps(trial_json))
        print("Logger stopped.")