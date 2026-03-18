
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


def calculate_lunch_break(shift_start: time, shift_end: time,
    duration_minutes: int = 60) -> Tuple[time, time]:
    dummy    = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy, shift_start)
    end_dt   = datetime.combine(dummy, shift_end)
    mid      = start_dt + (end_dt - start_dt) / 2
    earliest = datetime.combine(dummy, time(12, 0))
    ls = max(mid - timedelta(minutes=duration_minutes / 2), earliest)
    if ls.minute < 15:   ls = ls.replace(minute=0)
    elif ls.minute < 45: ls = ls.replace(minute=30)
    else:                ls = (ls + timedelta(hours=1)).replace(minute=0)
    return ls.time(), (ls + timedelta(minutes=duration_minutes)).time()

def generate_time_slots(
    working_days: List[int], day_names: List[str],
    shift_start: time, shift_end: time,
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
            if any(not (end.time() <= bs or now.time() >= be) for bs, be in break_periods):
                for bs, be in break_periods:
                    if now.time() < be:
                        now = datetime(2000, 1, 1, be.hour, be.minute)
                        break
                continue
            slots.append(Slot(id=gid, day_index=day_idx, day_name=day_name,
                              slot_index=sidx, start_time=now.time(),
                              end_time=end.time(), duration_minutes=slot_duration_minutes))
            gid += 1; sidx += 1; now = end
    return slots

def check_feasibility(data: MinimalData) -> Tuple[bool, str]:
    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]

    valid_by_dur: Dict[int, list] = {}
    for dur in set(data.subject_durations.values()) | {1}:
        vs = [s for s in range(num_slots - dur + 1)
              if slot_to_day[s] == slot_to_day[s + dur - 1]
              and (dur != 2 or data.slots[s].end_time == data.slots[s + 1].start_time)]
        valid_by_dur[dur] = vs
        if not vs:
            return False, f"No valid start slots for duration={dur}."

    for sec in data.sections:
        needed = sum(data.subject_durations.get(sub, 1) * c
                     for sub, c in data.hours[sec].items())
        if needed > num_slots:
            return False, f"Section '{sec}' needs {needed} slots, only {num_slots} exist."

    for sub in data.subjects:
        if not data.competencies.get(sub):
            return False, f"Subject '{sub}' has no teachers."
        sub_type = data.subject_types.get(sub)
        if not any(data.room_types.get(r) == sub_type for r in data.rooms):
            return False, f"Subject '{sub}' needs room type '{sub_type}' — none found."

    teacher_load: Dict[str, int] = defaultdict(int)
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            teachers = data.competencies.get(sub, [])
            if len(teachers) == 1:
                teacher_load[teachers[0]] += data.subject_durations.get(sub, 1) * count
    for t, l in teacher_load.items():
        if l > num_slots:
            return False, f"Teacher '{t}' sole-teaches {l} SU > {num_slots} slots."

    type_load: Dict[str, int] = defaultdict(int)
    type_cap:  Dict[str, int] = defaultdict(int)
    for r, rt in data.room_types.items():
        type_cap[rt] += num_slots
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            rt = data.subject_types.get(sub)
            if rt:
                type_load[rt] += data.subject_durations.get(sub, 1) * count
    for rt, load in type_load.items():
        if load > type_cap[rt]:
            return False, f"Room type '{rt}': demand {load} > capacity {type_cap[rt]}."

    return True, ""

def preassign_resources(data: MinimalData
) -> Tuple[Dict[Tuple[str,str], str], Dict[Tuple[str,str], str]]:
    teacher_map: Dict[Tuple[str,str], str] = {}
    t_load: Dict[str, int] = defaultdict(int)
    for sub in data.subjects:
        teachers = data.competencies.get(sub, [])
        if not teachers:
            continue
        for sec in sorted(data.sections):
            chosen = min(teachers, key=lambda t: t_load[t])
            teacher_map[(sec, sub)] = chosen
            t_load[chosen] += (data.subject_durations.get(sub, 1) *
                               data.hours[sec].get(sub, 0))

    rooms_by_type: Dict[str, List[str]] = defaultdict(list)
    for r in data.rooms:
        rooms_by_type[data.room_types[r]].append(r)

    room_map: Dict[Tuple[str,str], str] = {}
    r_ctr: Dict[str, int] = defaultdict(int)
    for sub in data.subjects:
        sub_type = data.subject_types.get(sub, "THEORY")
        avail = rooms_by_type.get(sub_type, [])
        if not avail:
            continue
        for sec in sorted(data.sections):
            room_map[(sec, sub)] = avail[r_ctr[sub_type] % len(avail)]
            r_ctr[sub_type] += 1

    return teacher_map, room_map


def get_on_day_bool(model, starts, instances, valid_by_dur,
                    valid_by_day_dur, cache, i, day):
    """
    Returns BoolVar b such that:
      b = 1  <=>  starts[i] is a valid start on `day`

    Encoding uses only model.add(expr >= k) / model.add(expr <= k)
    with .only_enforce_if(), which is stable across all OR-Tools v9.x.

    Strategy:
      • Collect day_vals  = valid start positions on `day` for this dur
      • Collect other_vals = valid start positions on other days
      • b=1  =>  starts[i] in day_vals
                 encoded as: starts[i] >= min(day_vals) AND starts[i] <= max(day_vals)
                 PLUS an exact-domain check via auxiliary all-diff if needed.
      • b=0  =>  starts[i] in other_vals
                 same range approach.

    For the typical case the slots within a day ARE contiguous in global
    index (day d occupies globals [d*spd .. (d+1)*spd - 1]), so min/max
    range is exact.  We assert this and use range encoding.
    """
    key = (i, day)
    if key in cache:
        return cache[key]

    dur        = instances[i]["dur"]
    day_vals   = valid_by_day_dur.get((day, dur), [])
    all_vals   = valid_by_dur[dur]
    other_vals = [s for s in all_vals if s not in set(day_vals)]

    b = model.new_bool_var(f"od_{i}_{day}")

    if not day_vals:
        model.add(b == 0)
        cache[key] = b
        return b

    day_lo, day_hi = min(day_vals), max(day_vals)

    model.add(starts[i] >= day_lo).only_enforce_if(b)
    model.add(starts[i] <= day_hi).only_enforce_if(b)

    if other_vals:
        other_lo, other_hi = min(other_vals), max(other_vals)
        model.add(starts[i] >= other_lo).only_enforce_if(b.negated())
        model.add(starts[i] <= other_hi).only_enforce_if(b.negated())

    cache[key] = b
    return b


def run_solver_internal(data: MinimalData) -> List[dict]:

    print("🔍 Running feasibility checks...")
    ok, reason = check_feasibility(data)
    if not ok:
        print(f"  ❌ {reason}"); return []
    print("✅ Data checks passed.\n")

    teacher_map, room_map = preassign_resources(data)
    print("👩‍🏫 Teachers + rooms pre-assigned.")

    W = len(data.slots)
    t_load: Dict[str, int] = defaultdict(int)
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            t = teacher_map.get((sec, sub))
            if t:
                t_load[t] += data.subject_durations.get(sub, 1) * count
    overloaded = [(t, l) for t, l in t_load.items() if l > W]
    if overloaded:
        for t, l in overloaded:
            print(f"  ❌ Teacher '{t}' has {l} SU > {W}.")
        print(f"  Formula: n_teachers >= ceil(sections × credits × dur / (0.45 × {W}))")
        return []

    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]
    unique_days = sorted(set(slot_to_day))
    spd         = sum(1 for s in data.slots if s.day_index == unique_days[0])

    valid_by_dur: Dict[int, list] = {}
    for dur in set(data.subject_durations.values()) | {1}:
        valid_by_dur[dur] = [
            s for s in range(num_slots - dur + 1)
            if slot_to_day[s] == slot_to_day[s + dur - 1]
            and (dur != 2 or data.slots[s].end_time == data.slots[s + 1].start_time)
        ]

    valid_by_day_dur: Dict[Tuple[int,int], List[int]] = {}
    for dur in valid_by_dur:
        for day in unique_days:
            valid_by_day_dur[(day, dur)] = [
                s for s in valid_by_dur[dur] if slot_to_day[s] == day
            ]

    instances: list = []
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            dur    = data.subject_durations.get(sub, 1)
            is_lab = (data.subject_types.get(sub) == "LAB")
            for credit_idx in range(count):
                instances.append({
                    "sec": sec, "sub": sub, "dur": dur, "is_lab": is_lab,
                    "teacher": teacher_map.get((sec, sub), ""),
                    "room":    room_map.get((sec, sub), ""),
                    "credits": 1, "total_credits": count,
                    "credit_idx": credit_idx,
                })

    n = len(instances)
    print(f"📐 Instances: {n}  |  Pure scheduling\n")

    model  = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers  = 8
    solver.parameters.log_search_progress = True
    solver.parameters.cp_model_presolve   = True
    solver.parameters.symmetry_level      = 2

    starts    = []
    intervals = []
    for i, inst in enumerate(instances):
        start = model.new_int_var_from_domain(
            cp_model.Domain.from_values(valid_by_dur[inst["dur"]]), f"s_{i}")
        starts.append(start)
        intervals.append(
            model.new_interval_var(start, inst["dur"], start + inst["dur"], f"iv_{i}"))

    sec_grp: Dict[str, list] = defaultdict(list)
    tch_grp: Dict[str, list] = defaultdict(list)
    rom_grp: Dict[str, list] = defaultdict(list)
    for i, inst in enumerate(instances):
        sec_grp[inst["sec"]].append(intervals[i])
        tch_grp[inst["teacher"]].append(intervals[i])
        rom_grp[inst["room"]].append(intervals[i])
    for ivs in sec_grp.values():
        model.add_no_overlap(ivs)
    for ivs in tch_grp.values():
        if len(ivs) > 1: model.add_no_overlap(ivs)
    for ivs in rom_grp.values():
        if len(ivs) > 1: model.add_no_overlap(ivs)

    kf = lambda idx: (instances[idx]["sec"], instances[idx]["sub"])
    for _, grp in groupby(sorted(range(n), key=kf), key=kf):
        g = list(grp)
        for a, b in zip(g, g[1:]):
            model.add(starts[a] <= starts[b])

    od_cache: Dict[Tuple[int,int], object] = {}

    def od(i, day):
        return get_on_day_bool(model, starts, instances, valid_by_dur,
                               valid_by_day_dur, od_cache, i, day)

    print("Building H4 (max 2 same-subject per day)...")
    sec_sub_grp: Dict[Tuple[str,str], List[int]] = defaultdict(list)
    for i, inst in enumerate(instances):
        sec_sub_grp[(inst["sec"], inst["sub"])].append(i)

    for (sec, sub), grp in sec_sub_grp.items():
        if len(grp) < 3:
            continue
        dur = instances[grp[0]]["dur"]
        for day in unique_days:
            if not valid_by_day_dur.get((day, dur)):
                continue
            model.add(sum(od(i, day) for i in grp) <= 2)

    print("Building H5 (lab sessions on different days)...")
    for (sec, sub), grp in sec_sub_grp.items():
        if not instances[grp[0]]["is_lab"] or len(grp) < 2:
            continue
        for day in unique_days:
            if not valid_by_day_dur.get((day, 2)):
                continue
            model.add(sum(od(i, day) for i in grp) <= 1)

    print("Building H6 (daily theory cap ≤ 6)...")
    sec_theory_grp: Dict[str, List[int]] = defaultdict(list)
    for i, inst in enumerate(instances):
        if not inst["is_lab"]:
            sec_theory_grp[inst["sec"]].append(i)

    for sec, grp in sec_theory_grp.items():
        for day in unique_days:
            if not valid_by_day_dur.get((day, 1)):
                continue
            model.add(sum(od(i, day) for i in grp) <= 6)

    print(f"  on_day booleans created: {len(od_cache)}")

    print("Building soft objective...")
    PENALTY_GAP  = 15
    PENALTY_LOAD = 3
    BIG          = num_slots + 1

    obj_terms = []

    for i in range(n):
        obj_terms.append(starts[i])

    for sec in data.sections:
        sec_inst = [i for i, inst in enumerate(instances) if inst["sec"] == sec]

        for day in unique_days:
            can_be = [i for i in sec_inst
                      if valid_by_day_dur.get((day, instances[i]["dur"]))]
            if not can_be:
                continue

            theory_here = [i for i in can_be if not instances[i]["is_lab"]]
            if len(theory_here) > 5:
                el = model.new_int_var(0, 6, f"el_{sec}_{day}")
                model.add(el >= sum(od(i, day) for i in theory_here) - 5)
                obj_terms.append(el * PENALTY_LOAD)

            if len(can_be) < 3:
                continue

            earliest = model.new_int_var(0, num_slots,   f"ea_{sec}_{day}")
            latest   = model.new_int_var(0, num_slots,   f"la_{sec}_{day}")
            tot_dur  = model.new_int_var(0, spd * 2,     f"td_{sec}_{day}")
            any_on   = model.new_bool_var(f"any_{sec}_{day}")

            model.add(sum(od(i, day) for i in can_be) >= 1).only_enforce_if(any_on)
            model.add(sum(od(i, day) for i in can_be) == 0).only_enforce_if(any_on.negated())

            for i in can_be:
                dur = instances[i]["dur"]
                b   = od(i, day)

                model.add(earliest <= starts[i] + BIG - BIG * b)
                model.add(latest   >= starts[i] + dur - BIG + BIG * b)

            model.add(tot_dur == sum(instances[i]["dur"] * od(i, day) for i in can_be))

            span     = model.new_int_var(0, spd + 2, f"sp_{sec}_{day}")
            gap      = model.new_int_var(0, spd + 2, f"gp_{sec}_{day}")
            gap_exc  = model.new_int_var(0, spd + 2, f"gx_{sec}_{day}")

            model.add(span == latest - earliest).only_enforce_if(any_on)
            model.add(span == 0).only_enforce_if(any_on.negated())
            model.add(gap  == span - tot_dur).only_enforce_if(any_on)
            model.add(gap  == 0).only_enforce_if(any_on.negated())

            model.add(gap_exc >= gap - 2)
            obj_terms.append(gap_exc * PENALTY_GAP)

    print(f"  Total objective terms: {len(obj_terms)}")
    model.minimize(sum(obj_terms))

    print("\n🚀 Starting solver …")
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("❌ No solution found.")
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
        working_days=[0,1,2,3,4],
        day_names=["Monday","Tuesday","Wednesday","Thursday","Friday"],
        shift_start=shift_start, shift_end=shift_end,
        slot_duration_minutes=json_data["duration"],
        break_periods=[(lunch_start, lunch_end)], buffer_minutes=0,
    )

    sections = json_data["sections"]
    subjects = [s["name"] for s in json_data["subjects"]]
    subject_types     = {s["name"]: ("LAB" if s.get("is_lab") else "THEORY")
                         for s in json_data["subjects"]}
    subject_durations = {s["name"]: (2 if s.get("is_lab") else 1)
                         for s in json_data["subjects"]}

    faculty_list = [f["name"] for f in json_data["faculty"]]
    competencies: Dict[str, List[str]] = {sub: [] for sub in subjects}
    for fac in json_data["faculty"]:
        for sub in fac["subjects"]:
            if sub in competencies:
                competencies[sub].append(fac["name"])

    rooms: List[str] = []; room_types: Dict[str, str] = {}
    for rb in json_data["rooms"]:
        for r_num in range(rb["start"], rb["end"] + 1):
            rn = f"{rb['block']}-{r_num}"
            rooms.append(rn)
            room_types[rn] = "LAB" if "LAB" in rb["block"].upper() else "THEORY"

    user_hours = {sec: {s["name"]: s["credits"] for s in json_data["subjects"]}
                  for sec in sections}

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