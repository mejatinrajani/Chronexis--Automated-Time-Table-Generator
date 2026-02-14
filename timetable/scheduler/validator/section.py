# scheduler/validator/section.py
from .utils import group_by_key, format_error
from collections import defaultdict


def check_section_clashes(slots):
    errors = []
    section_slots = group_by_key(slots, "section_id")

    for section_id, s_slots in section_slots.items():
        time_assignments = defaultdict(list)

        for slot in s_slots:
            time_key = (slot["day_index"], slot["timeslot_id"])
            time_assignments[time_key].append(slot)

        for time_key, concurrent in time_assignments.items():
            if len(concurrent) > 1:
                subjects = [s["subject_id"] for s in concurrent]
                errors.append(format_error(
                    "SECTION_OVERLAP",
                    f"Section {section_id} has multiple subjects assigned at the same time",
                    section_id=section_id,
                    day_index=time_key[0],
                    timeslot_id=time_key[1],
                    conflicting_subjects=subjects
                ))

    return errors