import pytest
from datetime import time
from scheduler.slots.generator import generate_time_slots


def test_generates_expected_number_of_slots():
    config = {
        "working_days": [0, 1],
        "day_names": ["Mon", "Tue", "..."],
        "shift_start": time(9, 0),
        "shift_end": time(17, 0),
        "slot_duration_minutes": 60,
        "break_periods": [(time(13,0), time(14,0))],
        "buffer_minutes": 0,
    }
    slots = generate_time_slots(**config)
    # 8 hours - 1 hour break = 7 slots/day × 2 days = 14
    assert len(slots) == 14


def test_respects_break():
    config = {
        "working_days": [0],
        "day_names": ["Mon"],
        "shift_start": time(9, 0),
        "shift_end": time(11, 30),
        "slot_duration_minutes": 60,
        "break_periods": [(time(10, 0), time(11, 0))],
    }
    slots = generate_time_slots(**config)
    # Should have only 9-10 and 11-11:30 → 2 slots
    assert len(slots) == 2
    assert slots[0].start_time == time(9,0)
    assert slots[1].start_time == time(11,0)


def test_no_slots_on_non_working_days():
    slots = generate_time_slots(
        working_days=[0, 2, 4],  # Mon, Wed, Fri
        day_names=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        shift_start=time(9,0),
        shift_end=time(10,0),
        slot_duration_minutes=60,
        break_periods=[]
    )
    days = {s.day_index for s in slots}
    assert days == {0, 2, 4}