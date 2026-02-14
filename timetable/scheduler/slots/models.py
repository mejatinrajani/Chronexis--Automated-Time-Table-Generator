

from dataclasses import dataclass
from datetime import time, datetime, timedelta


@dataclass(frozen=True)
class Slot:
    day_index: int
    day_name: str
    slot_index: int
    start_time: time
    end_time: time
    duration_minutes: int

    @property
    def unique_id(self) -> str:
        """Simple string identifier, e.g. 'Mon_03_0900-0950'"""
        return f"{self.day_name[:3]}_{self.slot_index:02d}_{self.start_time.strftime('%H%M')}-{self.end_time.strftime('%H%M')}"