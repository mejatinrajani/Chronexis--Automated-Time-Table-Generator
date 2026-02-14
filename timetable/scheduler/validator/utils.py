# scheduler/validator/utils.py
from collections import defaultdict
from typing import List, Dict, Any, Tuple


def group_by_key(slots: List[Dict[str, Any]], key: str) -> Dict[Any, List[Dict[str, Any]]]:
    """Group slots by any key (faculty_id, section_id, room_id, etc.)"""
    grouped = defaultdict(list)
    for slot in slots:
        k = slot.get(key)
        if k is not None:
            grouped[k].append(slot)
    return dict(grouped)


def get_timeslot_key(slot: Dict[str, Any]) -> Tuple[int, int]:
    """Simple unique time identifier: (day_index, timeslot_index_in_day)"""
    # You can later make this more sophisticated
    return (slot["day_index"], slot["timeslot_id"] % 100)  # example logic


def format_error(error_type: str, message: str, **extra) -> dict:
    """Standard error format"""
    return {
        "type": error_type,
        "message": message,
        **extra
    }