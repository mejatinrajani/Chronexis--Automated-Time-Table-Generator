from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import random, string
from datetime import time, timedelta, datetime

# --- 1. Data Structures ---

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

# --- 2. Generators ---

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

# --- 3. Adapter for Custom Data ---

def solve_custom_timetable(json_data: dict):
    """
    Adapts the JSON payload from frontend to the OR-Tools Solver Logic.
    """
    # 1. Time Setup
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

    # 2. Extract Data
    sections = json_data["sections"]
    
    subjects = [s["name"] for s in json_data["subjects"]]
    subject_types = {s["name"]: ("LAB" if s["is_lab"] else "THEORY") for s in json_data["subjects"]}
    subject_durations = {s["name"]: (2 if s["is_lab"] else 1) for s in json_data["subjects"]}
    
    # 3. Faculty & Competencies
    faculty_list = [f["name"] for f in json_data["faculty"]]
    competencies = {sub: [] for sub in subjects}
    
    for fac in json_data["faculty"]:
        for sub in fac["subjects"]:
            if sub in competencies:
                competencies[sub].append(fac["name"])

    # 4. Rooms
    rooms = []
    room_types = {}
    
    for r_block in json_data["rooms"]:
        for r_num in range(r_block["start"], r_block["end"] + 1):
            room_name = f"{r_block['block']}-{r_num}"
            rooms.append(room_name)
            # Simple heuristic for room types
            r_type = "LAB" if "LAB" in r_block["block"].upper() else "THEORY"
            room_types[room_name] = r_type

    # 5. Hours/Load
    user_hours = {}
    for sec in sections:
        credits = {}
        for sub_data in json_data["subjects"]:
            credits[sub_data["name"]] = sub_data["credits"]
        user_hours[sec] = credits

    # 6. Build Data Object
    data = MinimalData(
        sections=sections, subjects=subjects, slots=slots,
        faculty=faculty_list, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        competencies=competencies, unavailability={}, hours=user_hours,
        scheduling_style="COMPACT"
    )

    return run_solver_internal(data)

# --- 4. SOLVER LOGIC ---

def run_solver_internal(data: MinimalData):
    model = cp_model.CpModel()
    
    # Variables
    assign = {}      
    is_start = {}    
    assign_room = {} 
    fac_assign = {}  

    slots_by_day = {}
    for idx, s in enumerate(data.slots):
        slots_by_day.setdefault(s.day_index, []).append(idx)

    # --- 1. Variable Creation ---
    for sec in data.sections:
        for sub in data.hours[sec].keys():
            qualified = data.competencies.get(sub, [])
            # Allow fallback if no faculty (prevents crash, but might be unsolvable)
            if not qualified: 
                qualified = ["TBA"]
            
            for fac in qualified:
                fac_assign[(sec, sub, fac)] = model.NewBoolVar(f"f_{sec}_{sub}_{fac}")
            model.Add(sum(fac_assign[(sec, sub, fac)] for fac in qualified) == 1)

            sub_type = data.subject_types.get(sub, "THEORY")
            # If no specific room type found, assume THEORY rooms are valid
            valid_rooms = [r for r in data.rooms if data.room_types.get(r, "THEORY") == sub_type]
            if not valid_rooms: valid_rooms = ["TBA"]

            for s_idx in range(data.num_slots):
                assign[(sec, sub, s_idx)] = model.NewBoolVar(f"as_{sec}_{sub}_{s_idx}")
                is_start[(sec, sub, s_idx)] = model.NewBoolVar(f"st_{sec}_{sub}_{s_idx}")
                
                for r in valid_rooms:
                    assign_room[(sec, sub, r, s_idx)] = model.NewBoolVar(f"asr_{sec}_{sub}_{r}_{s_idx}")
                
                model.Add(assign[(sec, sub, s_idx)] == sum(assign_room[(sec, sub, r, s_idx)] for r in valid_rooms))

    # --- 2. Hard Constraints ---
    
    # Room Clash
    for r in data.rooms:
        for s_idx in range(data.num_slots):
            room_usage = [assign_room[(sec, sub, r, s_idx)] for sec in data.sections 
                          for sub in data.hours[sec].keys() if (sec, sub, r, s_idx) in assign_room]
            if room_usage: model.AddAtMostOne(room_usage)

    # Faculty Clash
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

    # Section Clash
    for sec in data.sections:
        for s_idx in range(data.num_slots):
            model.AddAtMostOne(assign[(sec, sub, s_idx)] for sub in data.hours[sec].keys())

    # Credit Hours & Duration Logic
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
            else: # Theory
                for s in range(data.num_slots):
                    model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])

    # --- 3. Objective Function ---
    obj_vars = []
    
    for sec in data.sections:
        for day_idx, indices in slots_by_day.items():
            is_occ = {s: model.NewBoolVar(f"o_{sec}_{s}") for s in indices}
            for s in indices:
                model.AddMaxEquality(is_occ[s], [assign[(sec, sub, s)] for sub in data.hours[sec].keys()])
            
            # Penalize late slots slightly to compact schedule
            for i, s_idx in enumerate(indices):
                obj_vars.append(is_occ[s_idx] * (i * 10)) 

    model.Minimize(sum(obj_vars))

    # --- 4. Solve ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0 
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)

    # --- 5. Extract Output ---
    output_data = []

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print(f"✅ Solver Status: {solver.StatusName(status)}")
        
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
                            
                            # --- CRITICAL KEYS FOR DB & VALIDATOR ---
                            "credits": data.hours[sec].get(sub, 3),        # Required by Database
                            "duration": data.subject_durations.get(sub, 1) # Required by Validator
                        })
    else:
        print("❌ No feasible solution found.")
        return []

    return output_data