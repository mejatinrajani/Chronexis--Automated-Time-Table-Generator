# scheduler/validator/__init__.py
from .faculty import check_faculty_clashes
from .section import check_section_clashes
from .room import check_room_conflicts, check_lab_room_compatibility
from .credits import check_subject_weekly_hours
from .labs import check_lab_continuity
from .breaks import check_no_class_during_break
from .daily_load import check_max_daily_hours_per_section
from .subject_distribution import check_no_same_subject_multiple_times_per_day
from .faculty_workload import calculate_faculty_back_to_back_penalty

ALL_VALIDATORS = [
    check_faculty_clashes,
    check_section_clashes,
    check_room_conflicts,
    check_lab_continuity,
    check_subject_weekly_hours,
    check_lab_room_compatibility,
    check_no_class_during_break,
    check_no_same_subject_multiple_times_per_day,
    check_max_daily_hours_per_section
]

def validate_timetable(slots, **kwargs):
    """
    Run all validators. 
    Simple validators get 'slots'. 
    Complex validators get 'slots' + their specific data from kwargs.
    """
    all_errors = []

    # 1. Run "Basic" validators (only need 'slots')
    all_errors.extend(check_faculty_clashes(slots))
    all_errors.extend(check_section_clashes(slots))
    all_errors.extend(check_room_conflicts(slots))
    all_errors.extend(check_lab_continuity(slots))

    # 2. Run "Data-Dependent" validators (only if data is provided in kwargs)
    
    # Check for Breaks
    if 'break_slots' in kwargs:
        all_errors.extend(check_no_class_during_break(slots, kwargs['break_slots']))
    
    # Check for Weekly Hours / Credits
    # Note: Use the key name you used in your test (credit_mapping)
    if 'credit_mapping' in kwargs:
        all_errors.extend(check_subject_weekly_hours(slots, kwargs['credit_mapping']))
        
    # Check for Lab Room Compatibility
    if 'room_info' in kwargs:
        all_errors.extend(check_lab_room_compatibility(slots, kwargs['room_info']))

    return all_errors