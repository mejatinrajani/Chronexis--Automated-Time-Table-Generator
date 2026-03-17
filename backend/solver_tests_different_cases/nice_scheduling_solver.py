from ortools.sat.python import cp_model
from typing import List, Dict, Tuple
from dataclasses import dataclass
import collections
from datetime import time, timedelta, datetime


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


def calculate_lunch_break(shift_start: time, shift_end: time, duration_minutes: int = 60) -> Tuple[time, time]:
    dummy = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy, shift_start)
    end_dt = datetime.combine(dummy, shift_end)
    mid = start_dt + (end_dt - start_dt) / 2
    earliest = datetime.combine(dummy, time(12, 0))
    lunch_start = max(mid - timedelta(minutes=duration_minutes / 2), earliest)

    if lunch_start.minute < 15:
        lunch_start = lunch_start.replace(minute=0)
    elif lunch_start.minute < 45:
        lunch_start = lunch_start.replace(minute=30)
    else:
        lunch_start = (lunch_start + timedelta(hours=1)).replace(minute=0)

    lunch_end = lunch_start + timedelta(minutes=duration_minutes)
    return lunch_start.time(), lunch_end.time()


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
    slots = []
    gid = 1
    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        now = datetime(2000, 1, 1, shift_start.hour, shift_start.minute)
        sidx = 0
        while now.time() < shift_end:
            end = now + timedelta(minutes=slot_duration_minutes)
            if end.time() > shift_end:
                break
            overlap_break = any(
                not (end.time() <= bs or now.time() >= be)
                for bs, be in break_periods
            )
            if overlap_break:
                for bs, be in break_periods:
                    if now.time() < be:
                        now = datetime(2000, 1, 1, be.hour, be.minute)
                        break
                continue
            slots.append(Slot(
                id=gid,
                day_index=day_idx,
                day_name=day_name,
                slot_index=sidx,
                start_time=now.time(),
                end_time=end.time(),
                duration_minutes=slot_duration_minutes
            ))
            gid += 1
            sidx += 1
            now = end
    return slots


def check_feasibility(data: MinimalData, available_slots_per_week: int):
    for sec in data.sections:
        total_credits = sum(data.hours[sec].values())
        if total_credits > available_slots_per_week:
            return False, f"Impossible Workload: Section '{sec}' needs {total_credits} slots, but only {available_slots_per_week} are available/week."

    subject_demand = {}
    for sec in data.sections:
        for sub, credits in data.hours[sec].items():
            subject_demand[sub] = subject_demand.get(sub, 0) + credits

    for sub, total_needed in subject_demand.items():
        teachers = data.competencies.get(sub, [])
        if not teachers:
            return False, f"Missing Faculty: Subject '{sub}' has no assigned faculty."

        capacity_per_teacher = available_slots_per_week
        total_capacity = len(teachers) * capacity_per_teacher
        if total_needed > total_capacity:
            return False, f"Faculty Overload: Subject '{sub}' needs {total_needed} slots, but {len(teachers)} teacher(s) only have {total_capacity} slots combined."

    total_slots_needed = sum(subject_demand.values())
    total_room_slots = len(data.rooms) * available_slots_per_week
    if total_slots_needed > total_room_slots:
        return False, f"Room Shortage: Total classes need {total_slots_needed} slots, but rooms only support {total_room_slots} slots."

    return True, "Math looks okay."

def run_solver_internal(data: MinimalData) -> List[dict]:
    from ortools.sat.python import cp_model
    import collections

    model = cp_model.CpModel()
    solver = cp_model.CpSolver()

    # ⚙️ Solver config
    solver.parameters.max_time_in_seconds = 120
    solver.parameters.num_search_workers = 8
    solver.parameters.cp_model_presolve = True

    num_slots = len(data.slots)

    # 🧠 Precompute
    slot_to_day = [s.day_index for s in data.slots]
    day_to_slots = collections.defaultdict(list)
    for i, s in enumerate(data.slots):
        day_to_slots[s.day_index].append(i)

    # 🧾 Build instances
    instances = []
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            dur = data.subject_durations.get(sub, 1)
            for _ in range(count):
                instances.append({
                    "sec": sec,
                    "sub": sub,
                    "dur": dur,
                    "credits": data.hours[sec][sub]
                })

    print(f"Instances: {len(instances)} | Slots: {num_slots}")

    # 🎯 Variables
    starts = []
    intervals = []

    for i, inst in enumerate(instances):
        dur = inst["dur"]

        valid_starts = []
        for s in range(num_slots - dur + 1):

            # same day constraint
            if slot_to_day[s] != slot_to_day[s + dur - 1]:
                continue

            # LAB: strict consecutive slots
            if dur == 2:
                if s + 1 >= num_slots:
                    continue
                if slot_to_day[s] != slot_to_day[s + 1]:
                    continue
                if data.slots[s + 1].slot_index != data.slots[s].slot_index + 1:
                    continue

            valid_starts.append(s)

        if not valid_starts:
            raise ValueError(f"No valid slot for {inst['sub']}")

        start = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues(valid_starts),
            f"start_{i}"
        )
        interval = model.NewIntervalVar(start, dur, start + dur, f"interval_{i}")

        starts.append(start)
        intervals.append(interval)

    # 👨‍🏫 Teacher assignment (simple for now)
    subject_teacher = {}
    for sub in data.subjects:
        teachers = data.competencies.get(sub, [])
        if not teachers:
            raise ValueError(f"No teacher for {sub}")
        subject_teacher[sub] = teachers[0]

    # 🏫 Rooms
    room_list = data.rooms
    room_index = {r: i for i, r in enumerate(room_list)}

    room_vars = []
    for i, inst in enumerate(instances):
        stype = data.subject_types.get(inst["sub"], "THEORY")

        valid_rooms = [
            room_index[r]
            for r in room_list
            if data.room_types.get(r, "THEORY") == stype
        ]

        room_var = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues(valid_rooms),
            f"room_{i}"
        )
        room_vars.append(room_var)

    # 🔒 HARD CONSTRAINTS

    # Section no overlap
    for sec in data.sections:
        model.AddNoOverlap([
            intervals[i] for i, inst in enumerate(instances)
            if inst["sec"] == sec
        ])

    # Teacher no overlap
    for teacher in data.faculty:
        model.AddNoOverlap([
            intervals[i] for i, inst in enumerate(instances)
            if subject_teacher[inst["sub"]] == teacher
        ])

    # Room no overlap
    for r in range(len(room_list)):
        room_intervals = []
        for i in range(len(instances)):
            is_r = model.NewBoolVar(f"is_r_{i}_{r}")

            model.Add(room_vars[i] == r).OnlyEnforceIf(is_r)
            model.Add(room_vars[i] != r).OnlyEnforceIf(is_r.Not())

            opt = model.NewOptionalIntervalVar(
                starts[i],
                instances[i]["dur"],
                starts[i] + instances[i]["dur"],
                is_r,
                f"room_interval_{i}_{r}"
            )
            room_intervals.append(opt)

        model.AddNoOverlap(room_intervals)

    # 🚫 SUBJECT CLUSTER PREVENTION (CRITICAL FIX)
    penalties = []

    for sec in data.sections:
        for sub in data.subjects:
            sub_idx = [
                i for i, inst in enumerate(instances)
                if inst["sec"] == sec and inst["sub"] == sub
            ]

            for i in range(len(sub_idx)):
                for j in range(i + 1, len(sub_idx)):
                    a = sub_idx[i]
                    b = sub_idx[j]

                    diff = model.NewIntVar(-num_slots, num_slots, f"diff_{a}_{b}")
                    model.Add(diff == starts[b] - starts[a])

                    too_close = model.NewBoolVar(f"close_{a}_{b}")
                    model.Add(diff <= 1).OnlyEnforceIf(too_close)

                    penalties.append(too_close * 50)

    # 🎯 COMPACT TIMETABLE
    for i in range(len(instances)):
        penalties.append(starts[i] * 2)

    model.Minimize(sum(penalties))

    # 🚀 Solve
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("❌ No solution found")
        return []

    print(f"✅ Solved | Objective: {solver.ObjectiveValue()}")

    # 📤 Output
    output = []
    for i, inst in enumerate(instances):
        s = solver.Value(starts[i])
        slot = data.slots[s]

        output.append({
            "section": inst["sec"],
            "subject": inst["sub"],
            "day": slot.day_name,
            "time": slot.start_time.strftime("%H:%M"),
            "teacher": subject_teacher[inst["sub"]],
            "room": data.rooms[solver.Value(room_vars[i])],
            "duration": inst["dur"],
            "credits": inst["credits"]
        })

    return output

def solve_custom_timetable(json_data: dict):
    s_h, s_m = map(int, json_data["start_time"].split(":"))
    e_h, e_m = map(int, json_data["end_time"].split(":"))
    shift_start = time(s_h, s_m)
    shift_end = time(e_h, e_m)
    
    lunch_start_time, lunch_end_time = calculate_lunch_break(shift_start, shift_end)
    
    slots = generate_time_slots(
        working_days=[0,1,2,3,4],
        day_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        shift_start=shift_start,
        shift_end=shift_end,
        slot_duration_minutes=json_data["duration"],
        break_periods=[(lunch_start_time, lunch_end_time)],
        buffer_minutes=0,
    )
    
    sections = json_data["sections"]
    subjects = [s["name"] for s in json_data["subjects"]]
    
    subject_types = {s["name"]: ("LAB" if s.get("is_lab", False) else "THEORY") for s in json_data["subjects"]}
    subject_durations = {s["name"]: (2 if s.get("is_lab", False) else 1) for s in json_data["subjects"]}
    
    faculty_list = [f["name"] for f in json_data["faculty"]]
    competencies = {sub: [] for sub in subjects}
    
    for fac in json_data["faculty"]:
        for sub in fac["subjects"]:
            if sub in competencies:
                competencies[sub].append(fac["name"])

    rooms = []
    room_types = {}
    for r_block in json_data["rooms"]:
        for r_num in range(r_block["start"], r_block["end"] + 1):
            room_name = f"{r_block['block']}-{r_num}"
            rooms.append(room_name)
            r_type = "LAB" if "LAB" in r_block["block"].upper() else "THEORY"
            room_types[room_name] = r_type

    user_hours = {}
    for sec in sections:
        credits = {}
        for sub_data in json_data["subjects"]:
            credits[sub_data["name"]] = sub_data["credits"]
        user_hours[sec] = credits

    data = MinimalData(
        sections=sections, subjects=subjects, slots=slots,
        faculty=faculty_list, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        competencies=competencies, unavailability={}, hours=user_hours,
        scheduling_style="COMPACT"
    )

    print("\n Running Feasibility Checks...")
    is_possible, reason = check_feasibility(data, len(slots) // 5 * 5) 
    if not is_possible:
        print(f" Feasibility Check Failed: {reason}")
        return []
    print("Math checks out. Starting Solver...")

    return run_solver_internal(data)

