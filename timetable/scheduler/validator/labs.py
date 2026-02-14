# scheduler/validator/labs.py

from collections import defaultdict
from .utils import group_by_key, format_error


def check_lab_continuity(slots, min_lab_hours=2):
    """
    Check that every lab session is continuous block of at least min_lab_hours
    
    Important: assumes timeslots are consecutive integers within a day
    """
    errors = []
    lab_assignments = defaultdict(list)

    # Group labs by (section, subject, faculty) - same lab session
    for slot in slots:
        if slot.get("is_lab"):
            key = (slot["section_id"], slot["subject_id"], slot["faculty_id"])
            lab_assignments[key].append(slot)

    for key, lab_slots in lab_assignments.items():
        # Sort by time
        sorted_slots = sorted(lab_slots, key=lambda s: (s["day_index"], s["timeslot_id"]))

        current_block = []
        for slot in sorted_slots:
            time_key = (slot["day_index"], slot["timeslot_id"])

            if not current_block:
                current_block.append(slot)
            else:
                prev = current_block[-1]
                prev_time = (prev["day_index"], prev["timeslot_id"])
                if time_key == (prev_time[0], prev_time[1] + 1):
                    current_block.append(slot)
                else:
                    # Check previous block size
                    if len(current_block) < min_lab_hours:
                        errors.append(format_error(
                            "LAB_NOT_CONTINUOUS",
                            f"Lab session too short ({len(current_block)}h) for section {key[0]} - {key[1]}",
                            section_id=key[0],
                            subject_id=key[1],
                            block_size=len(current_block),
                            min_required=min_lab_hours
                        ))
                    current_block = [slot]

        # Don't forget last block
        if current_block and len(current_block) < min_lab_hours:
            errors.append(format_error(
                "LAB_NOT_CONTINUOUS",
                f"Lab session too short ({len(current_block)}h) for section {key[0]} - {key[1]}",
                section_id=key[0],
                subject_id=key[1],
                block_size=len(current_block),
                min_required=min_lab_hours
            ))

    return errors