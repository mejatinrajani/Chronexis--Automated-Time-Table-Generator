# scheduler/validator/faculty_workload.py
from collections import defaultdict

def calculate_faculty_back_to_back_penalty(
    slots,
    penalty_per_back_to_back=5,
    consecutive_threshold=3  # classes in a row
):
    """
    Soft constraint: count consecutive classes without break
    Returns total penalty score (higher = worse)
    """
    faculty_day_slots = defaultdict(lambda: defaultdict(list))

    for slot in slots:
        fid = slot["faculty_id"]
        day = slot["day_index"]
        ts = slot["timeslot_id"]
        faculty_day_slots[fid][day].append(ts)

    total_penalty = 0

    for fid, days in faculty_day_slots.items():
        for day, timeslots in days.items():
            sorted_ts = sorted(set(timeslots))  # unique & ordered
            consecutive_count = 1
            for i in range(1, len(sorted_ts)):
                if sorted_ts[i] == sorted_ts[i-1] + 1:
                    consecutive_count += 1
                    if consecutive_count >= consecutive_threshold:
                        total_penalty += penalty_per_back_to_back
                else:
                    consecutive_count = 1

    return total_penalty