# tests/test_validators.py
import pytest
from collections import defaultdict
from scheduler.validator import (
    validate_timetable,
    check_subject_weekly_hours,
    check_lab_continuity,
    check_lab_room_compatibility,
    check_no_class_during_break,
    check_max_daily_hours_per_section,
    check_no_same_subject_multiple_times_per_day,
    calculate_faculty_back_to_back_penalty,
)


# ──────────────────────────────────────────────────────────────────────────────
# Base clean timetable + common helper
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_timetable():
    """Minimal valid timetable - no conflicts"""
    return [
        # Monday
        {"day_index": 0, "timeslot_id": 1, "section_id": 101, "subject_id": 501, "faculty_id": 11, "room_id": 201, "is_lab": False},
        {"day_index": 0, "timeslot_id": 2, "section_id": 101, "subject_id": 502, "faculty_id": 12, "room_id": 202, "is_lab": False},
        # Tuesday - lab block
        {"day_index": 1, "timeslot_id": 4, "section_id": 101, "subject_id": 601, "faculty_id": 16, "room_id": 301, "is_lab": True},
        {"day_index": 1, "timeslot_id": 5, "section_id": 101, "subject_id": 601, "faculty_id": 16, "room_id": 301, "is_lab": True},
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures for specific violations
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def timetable_with_credit_mismatch(clean_timetable):
    base = list(clean_timetable)
    # Add extra slot for subject 501 (should have 1, but now 2)
    base.append({
        "day_index": 0, "timeslot_id": 3, "section_id": 101, "subject_id": 501,
        "faculty_id": 13, "room_id": 203, "is_lab": False
    })
    return base


@pytest.fixture
def timetable_with_short_lab(clean_timetable):
    base = list(clean_timetable)
    # Only one slot lab instead of 2+
    base.append({
        "day_index": 2, "timeslot_id": 6, "section_id": 102, "subject_id": 602,
        "faculty_id": 17, "room_id": 302, "is_lab": True
    })
    return base


@pytest.fixture
def timetable_with_bad_lab_room(clean_timetable):
    base = list(clean_timetable)
    # Lab in normal theory room (room 203 is not lab)
    base[-1]["room_id"] = 203   # override last lab slot
    return base


@pytest.fixture
def timetable_during_break(clean_timetable):
    base = list(clean_timetable)
    # Class during lunch break (assume break is timeslot 3 on every day)
    base.append({
        "day_index": 0, "timeslot_id": 3, "section_id": 103, "subject_id": 503,
        "faculty_id": 18, "room_id": 204, "is_lab": False
    })
    return base


# ──────────────────────────────────────────────────────────────────────────────
# Required data for credit & lab room checks
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def subject_credit_mapping():
    """(section_id, subject_id) → expected weekly hours"""
    return {
        (101, 501): 1,
        (101, 502): 1,
        (101, 601): 2,
    }


@pytest.fixture
def room_info():
    """room_id → info dict"""
    return {
        201: {"is_lab": False, "name": "LT-101", "subject_specific": None},
        202: {"is_lab": False, "name": "CR-202", "subject_specific": None},
        301: {"is_lab": True, "name": "CS Lab", "subject_specific": "601"},
        302: {"is_lab": True, "name": "Generic Lab", "subject_specific": None},
        203: {"is_lab": False, "name": "CR-203", "subject_specific": None},
    }


@pytest.fixture
def break_slots():
    """List of forbidden timeslots (break periods)"""
    # Example: lunch break is timeslot 3 on every day
    return [
        {"day_index": 0, "timeslot_id": 3},
        {"day_index": 1, "timeslot_id": 3},
        {"day_index": 2, "timeslot_id": 3},
        # etc...
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_clean_timetable_has_no_errors(clean_timetable, subject_credit_mapping, room_info, break_slots):
    errors = validate_timetable(
        clean_timetable,
        credit_mapping=subject_credit_mapping,
        room_info=room_info,
        break_slots=break_slots
    )
    assert len(errors) == 0


def test_credit_mismatch_is_detected(timetable_with_credit_mismatch, subject_credit_mapping):
    errors = check_subject_weekly_hours(timetable_with_credit_mismatch, subject_credit_mapping)
    assert len(errors) >= 1
    assert any("CREDIT_MISMATCH" in e["type"] for e in errors)
    assert any(e.get("subject_id") == 501 for e in errors)


def test_short_lab_is_detected(timetable_with_short_lab):
    errors = check_lab_continuity(timetable_with_short_lab, min_lab_hours=2)
    assert len(errors) >= 1
    assert any("LAB_NOT_CONTINUOUS" in e["type"] for e in errors)


def test_bad_lab_room_is_detected(timetable_with_bad_lab_room, room_info):
    errors = check_lab_room_compatibility(timetable_with_bad_lab_room, room_info)
    assert len(errors) >= 1
    assert any("THEORY_ROOM_FOR_LAB" in e["type"] for e in errors)


def test_class_during_break_is_detected(timetable_during_break, break_slots):
    errors = check_no_class_during_break(timetable_during_break, break_slots)
    assert len(errors) >= 1
    assert any("CLASS_DURING_BREAK" in e["type"] for e in errors)


# Optional: more strict tests

def test_lab_in_subject_specific_room_is_accepted(clean_timetable, room_info):
    # Last lab is in "CS Lab" which is specific for subject 601
    errors = check_lab_room_compatibility(clean_timetable, room_info)
    assert len(errors) == 0   # or only warnings if you use them


def test_lab_in_generic_lab_is_warning_only(clean_timetable, room_info):
    # Change to generic lab
    clean_timetable[-1]["room_id"] = 302
    errors = check_lab_room_compatibility(clean_timetable, room_info)
    # Depending on your implementation:
    # either 0 errors + 1 warning, or just warning level
    assert not any(e["type"].endswith("_ERROR") for e in errors)  # no hard error

def test_max_daily_hours_ok(clean_timetable):
    errors = check_max_daily_hours_per_section(clean_timetable, max_hours_per_day=7)
    assert len(errors) == 0


def test_max_daily_hours_violated():
    slots = [
        {"day_index": 0, "section_id": 101, "duration_hours": 1.0} for _ in range(8)  # 8 hours
    ]
    errors = check_max_daily_hours_per_section(slots, max_hours_per_day=7)
    assert len(errors) >= 1
    assert "SECTION_OVERLOAD_DAY" in [e["type"] for e in errors]
    assert any(e["hours"] == 8.0 for e in errors)

def test_no_same_subject_per_day_ok(clean_timetable):
    errors = check_no_same_subject_multiple_times_per_day(clean_timetable)
    assert len(errors) == 0

def test_same_subject_same_day_detected(clean_timetable):
    # Pass fixture as argument and copy it
    slots = list(clean_timetable) 

    # Add a duplicate subject on the same day (Day 0)
    slots.append({
        "day_index": 0, 
        "section_id": 101, 
        "subject_id": 501, 
        "faculty_id": 11, 
        "room_id": 204,
        "is_lab": False
    })
    
    # FIX: Pass allow_if_credit_forced=False so it doesn't ignore the count of 2
    errors = check_no_same_subject_multiple_times_per_day(slots, allow_if_credit_forced=False)
    
    assert len(errors) >= 1
    assert any(e["type"] == "SAME_SUBJECT_SAME_DAY" for e in errors)

def test_back_to_back_penalty_calculation():
    # 4 consecutive classes
    slots = [
        {"faculty_id": 11, "day_index": 0, "timeslot_id": i} for i in range(1, 5)
    ]
    penalty = calculate_faculty_back_to_back_penalty(slots, penalty_per_back_to_back=5, consecutive_threshold=3)
    assert penalty >= 10  # at least 2 penalties (for 4th and maybe more)


def test_no_penalty_when_gaps():
    slots = [
        {"faculty_id": 11, "day_index": 0, "timeslot_id": 1},
        {"faculty_id": 11, "day_index": 0, "timeslot_id": 4},  # gap
        {"faculty_id": 11, "day_index": 0, "timeslot_id": 5},
    ]
    penalty = calculate_faculty_back_to_back_penalty(slots, consecutive_threshold=3)
    assert penalty == 0