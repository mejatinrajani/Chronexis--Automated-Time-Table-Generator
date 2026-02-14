def check_no_class_during_break(slots, break_slots):
    errors = []
    break_set = {(b["day_index"], b["timeslot_id"]) for b in break_slots}

    for s in slots:
        time_key = (s["day_index"], s["timeslot_id"])
        if time_key in break_set:
            errors.append({
                "type": "CLASS_DURING_BREAK",
                "message": "Class scheduled during break time",
                "day_index": s["day_index"],
                "timeslot_id": s["timeslot_id"]
            })
    return errors