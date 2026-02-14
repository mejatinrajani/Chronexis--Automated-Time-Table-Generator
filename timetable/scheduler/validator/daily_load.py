# scheduler/validator/daily_load.py
from collections import defaultdict
from .utils import format_error


def check_max_daily_hours_per_section(
    slots,
    max_hours_per_day=7,
    slot_duration_hours=1.0
):
    """
    No section should have more than max_hours_per_day of classes in one day
    """
    daily_load = defaultdict(lambda: defaultdict(float))

    for slot in slots:
        day = slot["day_index"]
        sec = slot["section_id"]
        # Real case: use actual duration from TimeSlot
        duration = slot.get("duration_hours", slot_duration_hours)
        daily_load[sec][day] += duration

    errors = []
    for section_id, days in daily_load.items():
        for day, hours in days.items():
            if hours > max_hours_per_day:
                errors.append(format_error(
                    "SECTION_OVERLOAD_DAY",
                    f"Section {section_id} exceeds max {max_hours_per_day}h on day {day} "
                    f"(has {hours:.1f}h)",
                    section_id=section_id,
                    day_index=day,
                    hours=hours,
                    max_allowed=max_hours_per_day
                ))

    return errors