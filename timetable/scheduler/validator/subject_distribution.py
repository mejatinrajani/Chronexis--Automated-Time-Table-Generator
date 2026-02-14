# scheduler/validator/subject_distribution.py
from collections import defaultdict
from .utils import format_error

def check_no_same_subject_multiple_times_per_day(slots, allow_if_credit_forced=True):
    """
    Try to avoid same subject more than once per day.
    Corrected: Uses 3 levels of nesting: Section -> Day -> Subject.
    """
    # Fix: Added an extra lambda to handle the third level (subject_id)
    day_subject = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for slot in slots:
        day = slot["day_index"]
        sec = slot["section_id"]
        sub = slot["subject_id"]
        
        # This will now work without TypeError
        day_subject[sec][day][sub] += 1

    errors = []
    # Loop through the three levels
    for section_id, days in day_subject.items():
        for day, subjects in days.items():
            for subject_id, count in subjects.items():
                if count > 1:
                    # Optional: allow if subject has very high credits
                    if allow_if_credit_forced and count <= 2:
                        continue
                        
                    errors.append(format_error(
                        "SAME_SUBJECT_SAME_DAY",
                        f"Section {section_id} has subject {subject_id} {count}x on day {day}",
                        section_id=section_id,
                        day_index=day,
                        subject_id=subject_id,
                        count=count
                    ))

    return errors