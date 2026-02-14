# scheduler/validator/faculty.py
from collections import defaultdict
from .utils import group_by_key, format_error


def check_faculty_clashes(slots):
    """
    No faculty should teach two different things at the same time
    Returns list of error dictionaries
    """
    errors = []
    faculty_slots = group_by_key(slots, "faculty_id")

    for faculty_id, f_slots in faculty_slots.items():
        time_assignments = defaultdict(list)

        for slot in f_slots:
            time_key = (slot["day_index"], slot["timeslot_id"])
            time_assignments[time_key].append(slot)

        for time_key, concurrent in time_assignments.items():
            if len(concurrent) > 1:
                sections = [s["section_id"] for s in concurrent]
                subjects = [s["subject_id"] for s in concurrent]
                errors.append(format_error(
                    "FACULTY_DOUBLE_BOOKED",
                    f"Faculty {faculty_id} is assigned to multiple classes at the same time slot",
                    faculty_id=faculty_id,
                    day_index=time_key[0],
                    timeslot_id=time_key[1],
                    conflicting_sections=sections,
                    conflicting_subjects=subjects
                ))

    return errors