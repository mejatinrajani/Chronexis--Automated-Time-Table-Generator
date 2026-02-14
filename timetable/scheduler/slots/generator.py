# scheduler/slots/generator.py
import os
import sys
import django

# 1. Add the project root to the Python path
# This moves up three levels from scheduler/solver/ to the root timetable_generator folder
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, "../../"))
sys.path.append(project_root)   

# 2. Tell Django which settings file to use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timetable.settings")

# 3. Initialize Django
django.setup()



from datetime import time, timedelta, datetime
from typing import List, Tuple, Dict, Optional
from scheduler.slots.models import Slot


def generate_time_slots(
    working_days: List[int],                     # [0,1,2,3,4] = Mon-Fri
    day_names: List[str],                       # ["Monday", "Tuesday", ...]
    shift_start: time,                          # e.g. time(8, 30)
    shift_end: time,                            # e.g. time(17, 0)
    slot_duration_minutes: int = 60,
    break_periods: List[Tuple[time, time]] = None,  # [(time(13,0), time(14,0)), ...]
    buffer_minutes: int = 0,                    # gap between slots
    min_slot_gap_minutes: int = 0               # minimal gap required
) -> List[Slot]:
    """
    Generate all possible valid teaching slots for the week
    """
    if break_periods is None:
        break_periods = []

    all_slots = []

    current_date = datetime(2000, 1, 3)  # arbitrary Monday - only time matters

    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        current_time = datetime.combine(current_date, next_start.time())

        slot_index = 0

        while current_time.time() < shift_end:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)

            overlaps_break = False
            for break_start, break_end in break_periods:
                if not (slot_end.time() <= break_start or current_time.time() >= break_end):
                    overlaps_break = True
                    break

            if not overlaps_break and slot_end.time() <= shift_end:
                slot = Slot(
                    day_index = day_idx,
                    day_name=day_name,
                    slot_index=slot_index,
                    start_time=current_time.time(),
                    end_time=slot_end.time(),
                    duration_minutes=slot_duration_minutes
                )
                all_slots.append(slot)
                slot_index += 1

            # Move to next possible start
            next_start = slot_end + timedelta(minutes=buffer_minutes + min_slot_gap_minutes)
            current_time = datetime.combine(current_date, next_start.time())

            # If next start would go beyond shift end, stop
            if next_start.time() >= shift_end:
                break

    return all_slots

if __name__ == "main":
    data = (generate_time_slots())
    print(data)