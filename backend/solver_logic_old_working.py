from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import random, string
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

    def to_dict(self):
        return {
            "id": self.id,
            "day_index": self.day_index,
            "day_name": self.day_name,
            "start_time": self.start_time.strftime("%H:%M"),
            "end_time": self.end_time.strftime("%H:%M"),
        }

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

    @property
    def num_slots(self):
        return len(self.slots)


def calculate_lunch_break(shift_start: time, shift_end: time, duration_minutes: int = 60) -> List[Tuple[time, time]]:
    dummy_date = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy_date, shift_start)
    end_dt = datetime.combine(dummy_date, shift_end)
    total_seconds = (end_dt - start_dt).total_seconds()
    midpoint_dt = start_dt + timedelta(seconds=total_seconds / 2)
    earliest_lunch = datetime.combine(dummy_date, time(12, 0))
    lunch_start_dt = max(midpoint_dt - timedelta(minutes=duration_minutes / 2), earliest_lunch)
    
    if lunch_start_dt.minute < 15: lunch_start_dt = lunch_start_dt.replace(minute=0)
    elif lunch_start_dt.minute < 45: lunch_start_dt = lunch_start_dt.replace(minute=30)
    else: lunch_start_dt = (lunch_start_dt + timedelta(hours=1)).replace(minute=0)

    lunch_end_dt = lunch_start_dt + timedelta(minutes=duration_minutes)
    return [(lunch_start_dt.time(), lunch_end_dt.time())]

def generate_time_slots(
    working_days: List[int],
    day_names: List[str],
    shift_start: time,
    shift_end: time,
    slot_duration_minutes: int = 50,
    break_periods: List[Tuple[time, time]] = None,
    buffer_minutes: int = 0,
    min_slot_gap_minutes: int = 0
) -> List[Slot]:
    if break_periods is None: break_periods = []
    all_slots = []
    current_date = datetime(2000, 1, 3)
    global_id_counter = 1

    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        current_time = datetime.combine(current_date, shift_start)
        slot_index = 0

        while current_time.time() < shift_end:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)
            if slot_end.time() > shift_end: break

            overlaps_break = False
            for break_start, break_end in break_periods:
                if not (slot_end.time() <= break_start or current_time.time() >= break_end):
                    overlaps_break = True
                    current_time = datetime.combine(current_date, break_end)
                    break

            if overlaps_break: continue

            slot = Slot(
                id=global_id_counter,
                day_index=day_idx,
                day_name=day_name,
                slot_index=slot_index,
                start_time=current_time.time(),
                end_time=slot_end.time(),
                duration_minutes=slot_duration_minutes
            )
            all_slots.append(slot)
            global_id_counter += 1
            slot_index += 1
            current_time = slot_end + timedelta(minutes=buffer_minutes + min_slot_gap_minutes)

    return all_slots



def check_feasibility(data: MinimalData, available_slots_per_week: int):
    """
    Performs quick math checks to see if a solution is even possible.
    Returns: (is_feasible: bool, reason: str)
    """

    for sec in data.sections:
        total_credits = sum(data.hours[sec].values())
        if total_credits > available_slots_per_week:
            return False, f"Impossible Workload: Section '{sec}' needs {total_credits} slots, but only {available_slots_per_week} are available/week."


    subject_demand = {}
    for sec in data.sections:
        for sub, credits in data.hours[sec].items():
            subject_demand[sub] = subject_demand.get(sub, 0) + credits

    teacher_load = {}
    for sub, total_needed in subject_demand.items():
        teachers = data.competencies.get(sub, [])
        if not teachers:
            return False, f"Missing Faculty: Subject '{sub}' has no assigned faculty."
        
        capacity_per_teacher = available_slots_per_week
        total_capacity = len(teachers) * capacity_per_teacher
        
        if total_needed > total_capacity:
            return False, f"Faculty Overload: Subject '{sub}' needs {total_needed} slots (across all sections), but the {len(teachers)} teacher(s) only have {total_capacity} slots combined."

    total_slots_needed = sum(subject_demand.values())
    total_room_slots = len(data.rooms) * available_slots_per_week
    
    if total_slots_needed > total_room_slots:
        return False, f"Room Shortage: Total classes need {total_slots_needed} slots, but rooms only support {total_room_slots} slots."

    return True, "Math looks okay."


def solve_custom_timetable(json_data: dict):
    
    s_h, s_m = map(int, json_data["start_time"].split(":"))
    e_h, e_m = map(int, json_data["end_time"].split(":"))
    shift_start = time(s_h, s_m)
    shift_end = time(e_h, e_m)
    
    lunch = calculate_lunch_break(shift_start, shift_end)
    
    slots = generate_time_slots(
        working_days=[0,1,2,3,4],
        day_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        shift_start=shift_start, shift_end=shift_end,
        slot_duration_minutes=json_data["duration"],
        break_periods=lunch
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


def run_solver_internal(data: MinimalData):
    model = cp_model.CpModel()
    
    assign = {}      
    is_start = {}    
    assign_room = {} 
    fac_assign = {}  

    slots_by_day = {}
    for idx, s in enumerate(data.slots):
        slots_by_day.setdefault(s.day_index, []).append(idx)

    for sec in data.sections:
        for sub in data.hours[sec].keys():
            qualified = data.competencies.get(sub, [])
            if not qualified: 
                qualified = ["TBA"]
            
            for fac in qualified:
                fac_assign[(sec, sub, fac)] = model.NewBoolVar(f"f_{sec}_{sub}_{fac}")
            model.Add(sum(fac_assign[(sec, sub, fac)] for fac in qualified) == 1)

            sub_type = data.subject_types.get(sub, "THEORY")
            valid_rooms = [r for r in data.rooms if data.room_types.get(r, "THEORY") == sub_type]
            if not valid_rooms: valid_rooms = ["TBA"]

            for s_idx in range(data.num_slots):
                assign[(sec, sub, s_idx)] = model.NewBoolVar(f"as_{sec}_{sub}_{s_idx}")
                is_start[(sec, sub, s_idx)] = model.NewBoolVar(f"st_{sec}_{sub}_{s_idx}")
                
                for r in valid_rooms:
                    assign_room[(sec, sub, r, s_idx)] = model.NewBoolVar(f"asr_{sec}_{sub}_{r}_{s_idx}")
                
                model.Add(assign[(sec, sub, s_idx)] == sum(assign_room[(sec, sub, r, s_idx)] for r in valid_rooms))

    for r in data.rooms:
        for s_idx in range(data.num_slots):
            room_usage = [assign_room[(sec, sub, r, s_idx)] for sec in data.sections 
                          for sub in data.hours[sec].keys() if (sec, sub, r, s_idx) in assign_room]
            if room_usage: model.AddAtMostOne(room_usage)

    for fac in data.faculty:
        for s_idx in range(data.num_slots):
            fac_usage = []
            for sec in data.sections:
                for sub in data.hours[sec].keys():
                    if fac in data.competencies.get(sub, []):
                        is_busy = model.NewBoolVar(f"b_{fac}_{sec}_{sub}_{s_idx}")
                        model.AddBoolAnd([assign[(sec, sub, s_idx)], fac_assign[(sec, sub, fac)]]).OnlyEnforceIf(is_busy)
                        model.AddBoolOr([assign[(sec, sub, s_idx)].Not(), fac_assign[(sec, sub, fac)].Not()]).OnlyEnforceIf(is_busy.Not())
                        fac_usage.append(is_busy)
            if fac_usage: model.AddAtMostOne(fac_usage)

    for sec in data.sections:
        for s_idx in range(data.num_slots):
            model.AddAtMostOne(assign[(sec, sub, s_idx)] for sub in data.hours[sec].keys())

    for sec in data.sections:
        for sub, credits in data.hours[sec].items():
            model.Add(sum(is_start[(sec, sub, s)] for s in range(data.num_slots)) == credits)
            
            duration = data.subject_durations.get(sub, 1)
            
            if duration == 2: # Lab
                for s in range(data.num_slots):
                    if s == 0: 
                        model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])
                    else: 
                        model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)] + is_start[(sec, sub, s-1)])
                for day_idx, indices in slots_by_day.items():
                    model.Add(is_start[(sec, sub, indices[-1])] == 0)
            else: 
                for s in range(data.num_slots):
                    model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])

    obj_vars = []
    
    for sec in data.sections:
        for day_idx, indices in slots_by_day.items():
            is_occ = {s: model.NewBoolVar(f"o_{sec}_{s}") for s in indices}
            for s in indices:
                model.AddMaxEquality(is_occ[s], [assign[(sec, sub, s)] for sub in data.hours[sec].keys()])
            
            for i, s_idx in enumerate(indices):
                obj_vars.append(is_occ[s_idx] * (i * 10)) 

    model.Minimize(sum(obj_vars))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0 
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)

    output_data = []

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print(f"Solver Status: {solver.StatusName(status)}")
        
        for sec in data.sections:
            for sub in data.hours[sec].keys():
                assigned_prof = "Staff"
                qualified = data.competencies.get(sub, [])
                if not qualified: qualified = ["TBA"]
                
                for fac in qualified:
                    if (sec, sub, fac) in fac_assign and solver.Value(fac_assign[(sec, sub, fac)]) == 1:
                        assigned_prof = fac
                        break
                
                for idx, slot in enumerate(data.slots):
                    if solver.Value(assign[(sec, sub, idx)]) == 1:
                        assigned_room = "TBA"
                        sub_type = data.subject_types.get(sub, "THEORY")
                        valid_rooms = [r for r in data.rooms if data.room_types.get(r) == sub_type]
                        
                        for r in valid_rooms:
                            if (sec, sub, r, idx) in assign_room and solver.Value(assign_room[(sec, sub, r, idx)]) == 1:
                                assigned_room = r
                                break
                        
                        output_data.append({
                            "id": f"{sec}-{sub}-{idx}",
                            "section": sec,
                            "day": slot.day_name,
                            "time": slot.start_time.strftime("%H:%M"),
                            "subject": sub,
                            "teacher": assigned_prof,
                            "room": assigned_room,
                            
                            "credits": data.hours[sec].get(sub, 3),        
                            "duration": data.subject_durations.get(sub, 1) 
                        })
    else:
        print(" No feasible solution found.")
        return []

    return output_data