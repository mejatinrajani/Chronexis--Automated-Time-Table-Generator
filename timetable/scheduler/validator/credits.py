# scheduler/validator/credits.py

from collections import defaultdict
from .utils import format_error


def check_subject_weekly_hours(slots, mapping=None):
    """
    Check that each section-subject pair has correct number of weekly slots
    
    Args:
        slots: list of assigned slot dicts
        mapping: optional dict {(section_id, subject_id): required_hours}
                 if None → we'll need to fetch from SectionSubjectMap later
    """
    if mapping is None:
        # In real system this should come from database
        # For now we can pass it or mock it
        mapping = {}

    actual_hours = defaultdict(int)

    for slot in slots:
        key = (slot["section_id"], slot["subject_id"])
        # For now we assume 1 slot = 1 hour
        # Later we can use real duration from TimeSlot
        actual_hours[key] += 1

    errors = []

    # Check required vs actual
    for (sec, sub), required in mapping.items():
        got = actual_hours.get((sec, sub), 0)
        if got != required:
            errors.append(format_error(
                "CREDIT_MISMATCH",
                f"Section {sec} - Subject {sub}: expected {required} hours, got {got}",
                section_id=sec,
                subject_id=sub,
                expected=required,
                actual=got
            ))

    # Also detect extra assignments (bonus check)
    for (sec, sub), count in actual_hours.items():
        if (sec, sub) not in mapping:
            errors.append(format_error(
                "UNEXPECTED_ASSIGNMENT",
                f"Section {sec} - Subject {sub}: unexpected {count} hours assigned",
                section_id=sec,
                subject_id=sub
            ))

    return errors