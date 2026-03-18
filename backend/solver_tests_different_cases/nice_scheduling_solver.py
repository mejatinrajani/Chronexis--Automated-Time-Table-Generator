
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import time, timedelta, datetime
from itertools import groupby
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model

@dataclass
class Slot:
    id: int
    day_index: int
    day_name: str
    slot_index: int
    start_time: time
    end_time: time
    duration_minutes: int


@dataclass
class MinimalData:
    sections: List[str]
    subjects: List[str]
    slots: List[Slot]
    faculty: List[str]
    rooms: List[str]
    room_types: Dict[str, str]
    subject_types: Dict[str, str]
    subject_durations: Dict[str, int]
    competencies: Dict[str, List[str]]
    unavailability: Dict[str, List[int]]
    hours: Dict[str, Dict[str, int]]
    scheduling_style: str



def calculate_lunch_break(
    shift_start: time, shift_end: time, duration_minutes: int = 60
) -> Tuple[time, time]:
    dummy    = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy, shift_start)
    end_dt   = datetime.combine(dummy, shift_end)
    mid      = start_dt + (end_dt - start_dt) / 2
    earliest = datetime.combine(dummy, time(12, 0))
    ls = max(mid - timedelta(minutes=duration_minutes / 2), earliest)
    if ls.minute < 15:
        ls = ls.replace(minute=0)
    elif ls.minute < 45:
        ls = ls.replace(minute=30)
    else:
        ls = (ls + timedelta(hours=1)).replace(minute=0)
    return ls.time(), (ls + timedelta(minutes=duration_minutes)).time()


def generate_time_slots(
    working_days: List[int],
    day_names: List[str],
    shift_start: time,
    shift_end: time,
    slot_duration_minutes: int = 50,
    break_periods: List[Tuple[time, time]] = None,
    buffer_minutes: int = 5,
) -> List[Slot]:
    if break_periods is None:
        break_periods = []
    slots, gid = [], 1
    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        now = datetime(2000, 1, 1, shift_start.hour, shift_start.minute)
        sidx = 0
        while now.time() < shift_end:
            end = now + timedelta(minutes=slot_duration_minutes)
            if end.time() > shift_end:
                break
            if any(not (end.time() <= bs or now.time() >= be)
                   for bs, be in break_periods):
                for bs, be in break_periods:
                    if now.time() < be:
                        now = datetime(2000, 1, 1, be.hour, be.minute)
                        break
                continue
            slots.append(Slot(
                id=gid, day_index=day_idx, day_name=day_name,
                slot_index=sidx, start_time=now.time(),
                end_time=end.time(), duration_minutes=slot_duration_minutes,
            ))
            gid += 1; sidx += 1; now = end
    return slots



def check_feasibility(data: MinimalData) -> Tuple[bool, str]:
    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]

    valid_starts_by_dur: Dict[int, list] = {}
    for dur in set(data.subject_durations.values()) | {1}:
        vs = [
            s for s in range(num_slots - dur + 1)
            if slot_to_day[s] == slot_to_day[s + dur - 1]
            and (dur != 2 or data.slots[s].end_time == data.slots[s + 1].start_time)
        ]
        valid_starts_by_dur[dur] = vs
        if not vs:
            return False, f"No valid start slots for duration={dur}."

    for sec in data.sections:
        needed = sum(
            data.subject_durations.get(sub, 1) * count
            for sub, count in data.hours[sec].items()
        )
        if needed > num_slots:
            return False, (
                f"Section '{sec}' needs {needed} slot-units "
                f"but only {num_slots} exist."
            )

    for sub in data.subjects:
        if not data.competencies.get(sub):
            return False, f"Subject '{sub}' has no competent teachers."
        sub_type = data.subject_types.get(sub)
        if not any(data.room_types.get(r) == sub_type for r in data.rooms):
            return False, (
                f"Subject '{sub}' needs room type '{sub_type}' "
                f"but no such rooms exist."
            )

    # Teacher overload check
    teacher_sole_load: Dict[str, int] = defaultdict(int)
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            dur = data.subject_durations.get(sub, 1)
            teachers = data.competencies.get(sub, [])
            if len(teachers) == 1:
                teacher_sole_load[teachers[0]] += dur * count

    for teacher, load in teacher_sole_load.items():
        if load > num_slots:
            return False, (
                f"Teacher '{teacher}' sole-teaches {load} slot-units "
                f"but only {num_slots} slots exist."
            )

    # Room type capacity
    type_load:  Dict[str, int] = defaultdict(int)
    type_rooms: Dict[str, int] = defaultdict(int)
    for r, rt in data.room_types.items():
        type_rooms[rt] += 1
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            rt = data.subject_types.get(sub)
            if rt:
                type_load[rt] += data.subject_durations.get(sub, 1) * count
    for rt, load in type_load.items():
        cap = type_rooms[rt] * num_slots
        if load > cap:
            return False, (
                f"Room type '{rt}': demand={load} > capacity={cap}."
            )

    return True, ""



def preassign_resources(
    data: MinimalData,
) -> Tuple[Dict[Tuple[str,str], str], Dict[Tuple[str,str], str]]:

    # Teacher assignment (round-robin by load) 
    teacher_map: Dict[Tuple[str,str], str] = {}
    teacher_load: Dict[str, int] = defaultdict(int)

    for sub in data.subjects:
        teachers = data.competencies.get(sub, [])
        if not teachers:
            continue
        for sec in sorted(data.sections):
            # Always pick the least-loaded eligible teacher
            chosen = min(teachers, key=lambda t: teacher_load[t])
            teacher_map[(sec, sub)] = chosen
            teacher_load[chosen] += (
                data.subject_durations.get(sub, 1) *
                data.hours[sec].get(sub, 0)
            )

    # Room assignment (round-robin by type) 
    # Group rooms by type
    rooms_by_type: Dict[str, List[str]] = defaultdict(list)
    for r in data.rooms:
        rooms_by_type[data.room_types[r]].append(r)

    room_map: Dict[Tuple[str,str], str] = {}
    room_counters: Dict[str, int] = defaultdict(int)  

    for sub in data.subjects:
        sub_type = data.subject_types.get(sub, "THEORY")
        available_rooms = rooms_by_type.get(sub_type, [])
        if not available_rooms:
            continue
        for sec in sorted(data.sections):
            idx = room_counters[sub_type] % len(available_rooms)
            room_map[(sec, sub)] = available_rooms[idx]
            room_counters[sub_type] += 1

    return teacher_map, room_map


def run_solver_internal(data: MinimalData) -> List[dict]:

    # 0. Pre-flight 
    print("🔍 Running feasibility checks...")
    ok, reason = check_feasibility(data)
    if not ok:
        print(f"  ❌ {reason}")
        return []
    print("✅ Data checks passed.\n")

    # 1. Pre-assign teachers and rooms 
    teacher_map, room_map = preassign_resources(data)
    print("👩‍🏫 Teachers + rooms pre-assigned.")

    # Verify teacher load after assignment
    W = len(data.slots)
    teacher_load: Dict[str, int] = defaultdict(int)
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            dur = data.subject_durations.get(sub, 1)
            t   = teacher_map.get((sec, sub))
            if t:
                teacher_load[t] += dur * count

    overloaded = [(t, l) for t, l in teacher_load.items() if l > W]
    if overloaded:
        for t, l in overloaded:
            print(f"  ❌ Teacher '{t}' has {l} slot-units > {W} available.")
        print("🛑 Add more teachers.")
        print(f"   Formula: n_teachers >= ceil(n_sections × credits × dur / (0.45 × {W}))")
        return []

    # 2. Build model 
    model  = cp_model.CpModel()
    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers  = 8
    solver.parameters.log_search_progress = True
    solver.parameters.cp_model_presolve   = True
    solver.parameters.symmetry_level      = 2

    # Slot metadata 
    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]

    valid_starts_by_dur: Dict[int, list] = {}
    for dur in set(data.subject_durations.values()) | {1}:
        valid_starts_by_dur[dur] = [
            s for s in range(num_slots - dur + 1)
            if slot_to_day[s] == slot_to_day[s + dur - 1]
            and (dur != 2 or data.slots[s].end_time == data.slots[s + 1].start_time)
        ]

    # Build instances 
    instances: list = []
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            dur     = data.subject_durations.get(sub, 1)
            teacher = teacher_map.get((sec, sub), "")
            room    = room_map.get((sec, sub), "")
            for credit_idx in range(count):
                instances.append({
                    "sec": sec, "sub": sub, "dur": dur,
                    "teacher": teacher,   # fixed constant
                    "room":    room,      # fixed constant
                    "credits": 1, "total_credits": count,
                    "credit_idx": credit_idx,
                })

    n = len(instances)
    print(f"📐 Instances: {n}  |  Boolean vars: 0  |  Pure scheduling problem")

    # Variables: start times only
    starts    = []
    intervals = []   
    for i, inst in enumerate(instances):
        start = model.new_int_var_from_domain(
            cp_model.Domain.from_values(valid_starts_by_dur[inst["dur"]]),
            f"s_{i}"
        )
        starts.append(start)
        intervals.append(
            model.new_interval_var(start, inst["dur"], start + inst["dur"], f"iv_{i}")
        )


    sec_groups:     Dict[str, list] = defaultdict(list)
    teacher_groups: Dict[str, list] = defaultdict(list)
    room_groups:    Dict[str, list] = defaultdict(list)

    for i, inst in enumerate(instances):
        sec_groups[inst["sec"]].append(intervals[i])
        teacher_groups[inst["teacher"]].append(intervals[i])
        room_groups[inst["room"]].append(intervals[i])

    for ivs in sec_groups.values():
        model.add_no_overlap(ivs)

    for ivs in teacher_groups.values():
        if len(ivs) > 1:
            model.add_no_overlap(ivs)

    for ivs in room_groups.values():
        if len(ivs) > 1:
            model.add_no_overlap(ivs)

    # Symmetry breaking: order identical (sec, sub) instances by start time
    key_fn = lambda idx: (instances[idx]["sec"], instances[idx]["sub"])
    for _, grp in groupby(sorted(range(n), key=key_fn), key=key_fn):
        g = list(grp)
        for a, b in zip(g, g[1:]):
            model.add(starts[a] <= starts[b])

    model.minimize(sum(starts))

    print("🚀 Starting solver …")
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("❌ No solution found.")
        print("   Room pre-assignment may have created conflicts.")
        print("   Check: are there enough rooms for concurrent peak demand?")
        print(f"   You need at least {len(data.sections)} rooms of each type.")
        return []

    print(f"✅ {solver.status_name(status)} | "
          f"Objective: {solver.objective_value:.0f} | "
          f"Wall time: {solver.wall_time:.1f}s")


    output = []
    for i, inst in enumerate(instances):
        s          = solver.value(starts[i])
        start_slot = data.slots[s]
        end_slot   = data.slots[s + inst["dur"] - 1]
        output.append({
            "section":       inst["sec"],
            "subject":       inst["sub"],
            "day":           start_slot.day_name,
            "start_time":    start_slot.start_time.strftime("%H:%M"),
            "end_time":      end_slot.end_time.strftime("%H:%M"),
            "teacher":       inst["teacher"],
            "room":          inst["room"],
            "duration":      inst["dur"],
            "credits":       inst["credits"],
            "total_credits": inst["total_credits"],
        })
    return output


def solve_custom_timetable(json_data: dict):
    s_h, s_m = map(int, json_data["start_time"].split(":"))
    e_h, e_m = map(int, json_data["end_time"].split(":"))
    shift_start = time(s_h, s_m)
    shift_end   = time(e_h, e_m)

    lunch_start, lunch_end = calculate_lunch_break(shift_start, shift_end)

    slots = generate_time_slots(
        working_days=[0, 1, 2, 3, 4],
        day_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        shift_start=shift_start,
        shift_end=shift_end,
        slot_duration_minutes=json_data["duration"],
        break_periods=[(lunch_start, lunch_end)],
        buffer_minutes=0,
    )

    sections = json_data["sections"]
    subjects = [s["name"] for s in json_data["subjects"]]

    subject_types     = {
        s["name"]: ("LAB" if s.get("is_lab", False) else "THEORY")
        for s in json_data["subjects"]
    }
    subject_durations = {
        s["name"]: (2 if s.get("is_lab", False) else 1)
        for s in json_data["subjects"]
    }

    faculty_list = [f["name"] for f in json_data["faculty"]]
    competencies: Dict[str, List[str]] = {sub: [] for sub in subjects}
    for fac in json_data["faculty"]:
        for sub in fac["subjects"]:
            if sub in competencies:
                competencies[sub].append(fac["name"])

    rooms:      List[str]        = []
    room_types: Dict[str, str]   = {}
    for r_block in json_data["rooms"]:
        for r_num in range(r_block["start"], r_block["end"] + 1):
            room_name = f"{r_block['block']}-{r_num}"
            rooms.append(room_name)
            room_types[room_name] = (
                "LAB" if "LAB" in r_block["block"].upper() else "THEORY"
            )

    user_hours = {
        sec: {s["name"]: s["credits"] for s in json_data["subjects"]}
        for sec in sections
    }

    data = MinimalData(
        sections=sections, subjects=subjects, slots=slots,
        faculty=faculty_list, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        competencies=competencies, unavailability={},
        hours=user_hours, scheduling_style="COMPACT",
    )

    print("\n Running Feasibility Checks...")
    ok, reason = check_feasibility(data)
    if not ok:
        print(f" Feasibility Check Failed: {reason}")
        return []
    print("Math checks out. Starting Solver...")

    return run_solver_internal(data)