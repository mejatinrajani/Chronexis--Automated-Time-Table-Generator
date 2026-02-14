# python manage.py shell, run the below program in python shell.
# from scheduler.validator import validate_timetable

# fake_slots = [
#     {"faculty_id": 1, "section_id": 7, "timeslot_id": 7, "day_index": 0, "room_id": 3, "subject_id": 10},
#     {"faculty_id": 2, "section_id": 6, "timeslot_id": 7, "day_index": 0, "room_id": 3, "subject_id": 11},
# ]

# errors = validate_timetable(fake_slots)
# print(errors)


#real tests using pytest
import pytest
from collections import defaultdict
from scheduler.validator import (
    validate_timetable,
    check_faculty_clashes,
    check_section_clashes,
    check_room_conflicts,
    check_lab_continuity,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures - reusable fake timetable data
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_timetable():
    """Basic valid timetable - no conflicts"""
    return [
        {"day_index": 0, "timeslot_id": 1, "section_id": 101, "subject_id": 501, "faculty_id": 11, "room_id": 201, "is_lab": False},
        {"day_index": 0, "timeslot_id": 2, "section_id": 101, "subject_id": 502, "faculty_id": 12, "room_id": 202, "is_lab": False},
        {"day_index": 0, "timeslot_id": 3, "section_id": 102, "subject_id": 501, "faculty_id": 11, "room_id": 203, "is_lab": False},
        {"day_index": 1, "timeslot_id": 1, "section_id": 101, "subject_id": 503, "faculty_id": 13, "room_id": 201, "is_lab": True},
        {"day_index": 1, "timeslot_id": 2, "section_id": 101, "subject_id": 503, "faculty_id": 13, "room_id": 201, "is_lab": True},
    ]


@pytest.fixture
def timetable_with_faculty_clash(clean_timetable):
    base = list(clean_timetable)
    # Faculty 11 is teaching two different sections at the same time
    base.append({
        "day_index": 0,
        "timeslot_id": 1,
        "section_id": 103,
        "subject_id": 504,
        "faculty_id": 11,           # ← conflict!
        "room_id": 204,
        "is_lab": False
    })
    return base


@pytest.fixture
def timetable_with_section_overlap(clean_timetable):
    base = list(clean_timetable)
    # Section 101 has two subjects at the same time
    base.append({
        "day_index": 0,
        "timeslot_id": 2,
        "section_id": 101,
        "subject_id": 505,          # ← overlap!
        "faculty_id": 14,
        "room_id": 205,
        "is_lab": False
    })
    return base


@pytest.fixture
def timetable_with_room_double_booking(clean_timetable):
    base = list(clean_timetable)
    # Room 201 is used by two different classes at the same time
    base.append({
        "day_index": 0,
        "timeslot_id": 1,
        "section_id": 104,
        "subject_id": 506,
        "faculty_id": 15,
        "room_id": 201,             # ← conflict!
        "is_lab": False
    })
    return base


@pytest.fixture
def timetable_with_short_lab():
    """For testing lab continuity"""
    return [
        # Normal theory
        {"day_index": 0, "timeslot_id": 1, "section_id": 101, "subject_id": 501, "faculty_id": 11, "room_id": 201, "is_lab": False},
        # Lab should be 2+ slots consecutive
        {"day_index": 1, "timeslot_id": 3, "section_id": 101, "subject_id": 601, "faculty_id": 16, "room_id": 301, "is_lab": True},
        {"day_index": 1, "timeslot_id": 5, "section_id": 101, "subject_id": 601, "faculty_id": 16, "room_id": 301, "is_lab": True},  # gap → should fail
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Tests - main validator pipeline
# ──────────────────────────────────────────────────────────────────────────────

def test_validate_timetable_clean(clean_timetable):
    errors = validate_timetable(clean_timetable)
    assert len(errors) == 0, "Clean timetable should have no errors"


def test_validate_timetable_faculty_clash(timetable_with_faculty_clash):
    errors = validate_timetable(timetable_with_faculty_clash)
    assert len(errors) >= 1
    assert any(e["type"] == "FACULTY_DOUBLE_BOOKED" for e in errors)


def test_validate_timetable_section_overlap(timetable_with_section_overlap):
    errors = validate_timetable(timetable_with_section_overlap)
    assert len(errors) >= 1
    assert any(e["type"] == "SECTION_OVERLAP" for e in errors)


def test_validate_timetable_room_conflict(timetable_with_room_double_booking):
    errors = validate_timetable(timetable_with_room_double_booking)
    assert len(errors) >= 1
    assert any(e["type"] == "ROOM_DOUBLE_BOOKED" for e in errors)


# ──────────────────────────────────────────────────────────────────────────────
# Granular / individual validator tests
# ──────────────────────────────────────────────────────────────────────────────

def test_check_faculty_clashes_no_conflict(clean_timetable):
    errors = check_faculty_clashes(clean_timetable)
    assert len(errors) == 0


def test_check_faculty_clashes_detects_conflict(timetable_with_faculty_clash):
    errors = check_faculty_clashes(timetable_with_faculty_clash)
    assert len(errors) >= 1
    assert "FACULTY_DOUBLE_BOOKED" in [e["type"] for e in errors]
    assert 11 in [e.get("faculty_id") for e in errors]  # the conflicting faculty


def test_check_section_clashes_no_conflict(clean_timetable):
    errors = check_section_clashes(clean_timetable)
    assert len(errors) == 0


def test_check_section_clashes_detects_overlap(timetable_with_section_overlap):
    errors = check_section_clashes(timetable_with_section_overlap)
    assert len(errors) >= 1
    assert "SECTION_OVERLAP" in [e["type"] for e in errors]
    assert 101 in [e.get("section_id") for e in errors]


def test_check_room_conflicts_no_conflict(clean_timetable):
    errors = check_room_conflicts(clean_timetable)
    assert len(errors) == 0


def test_check_room_conflicts_detects_double_booking(timetable_with_room_double_booking):
    errors = check_room_conflicts(timetable_with_room_double_booking)
    assert len(errors) >= 1
    assert "ROOM_DOUBLE_BOOKED" in [e["type"] for e in errors]


# ──────────────────────────────────────────────────────────────────────────────
# Lab continuity tests (uncomment when you implement check_lab_continuity)
# ──────────────────────────────────────────────────────────────────────────────

def test_lab_continuity_good_case():
    """Each unique lab session (subject 601 and 602) must meet the 2h block requirement."""
    slots = [
        # Lab 1: Subject 601 (2 hours) - OK
        {"day_index": 0, "timeslot_id": 4, "section_id": 101, "subject_id": 601, "faculty_id": 1, "is_lab": True},
        {"day_index": 0, "timeslot_id": 5, "section_id": 101, "subject_id": 601, "faculty_id": 1, "is_lab": True},
        # Lab 2: Subject 602 (2 hours) - OK
        {"day_index": 1, "timeslot_id": 1, "section_id": 101, "subject_id": 602, "faculty_id": 1, "is_lab": True},
        {"day_index": 1, "timeslot_id": 2, "section_id": 101, "subject_id": 602, "faculty_id": 1, "is_lab": True},
    ]
    errors = check_lab_continuity(slots, min_lab_hours=2)
    assert len(errors) == 0

def test_lab_continuity_detects_short_block():
    """Tests a case where a lab is only 1 hour long."""
    slots = [
        {"day_index": 1, "timeslot_id": 3, "section_id": 101, "subject_id": 601, "faculty_id": 16, "is_lab": True},
    ]
    errors = check_lab_continuity(slots, min_lab_hours=2)
    assert len(errors) >= 1
    assert "LAB_NOT_CONTINUOUS" in [e["type"] for e in errors]