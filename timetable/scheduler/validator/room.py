# scheduler/validator/room.py
from .utils import group_by_key, format_error
from collections import defaultdict


def check_room_conflicts(slots):
    errors = []
    room_slots = group_by_key(slots, "room_id")

    for room_id, r_slots in room_slots.items():
        time_assignments = defaultdict(list)

        for slot in r_slots:
            time_key = (slot["day_index"], slot["timeslot_id"])
            time_assignments[time_key].append(slot)

        for time_key, concurrent in time_assignments.items():
            if len(concurrent) > 1:
                sections = [s["section_id"] for s in concurrent]
                errors.append(format_error(
                    "ROOM_DOUBLE_BOOKED",
                    f"Room {room_id} is assigned to multiple classes simultaneously",
                    room_id=room_id,
                    day_index=time_key[0],
                    timeslot_id=time_key[1],
                    conflicting_sections=sections
                ))

    return errors


def check_lab_room_compatibility(slots, room_info=None):
    """
    Check that labs are preferably assigned to:
    1. Subject-specific lab (e.g. "Physics Lab", "CS301 Lab")
    2. Generic lab room
    3. Theory room (only as last resort)
    
    room_info: dict {room_id: {"is_lab": bool, "name": str, "subject_specific": str or None}}
    """
    if room_info is None:
        room_info = {}  # In real code → fetch from Room model

    errors = []
    warnings = []

    for slot in slots:
        if not slot.get("is_lab"):
            continue

        room_id = slot["room_id"]
        subject_id = slot["subject_id"]
        section_id = slot["section_id"]

        info = room_info.get(room_id, {"is_lab": False, "name": "Unknown", "subject_specific": None})

        if info["subject_specific"] == str(subject_id):
            continue  # Perfect match - subject specific lab

        elif info["is_lab"]:
            warnings.append(format_error(
                "GENERIC_LAB_USED",
                f"Section {section_id} lab used generic lab room {room_id}",
                level="warning"
            ))

        else:
            # Theory room used for lab - this should be error in strict mode
            errors.append(format_error(
                "THEORY_ROOM_FOR_LAB",
                f"Lab assigned to theory room {room_id} (section {section_id}, subject {subject_id})",
                room_id=room_id,
                section_id=section_id,
                subject_id=subject_id
            ))

    return errors + warnings