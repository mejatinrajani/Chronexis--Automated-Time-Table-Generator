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

# --- 3. Data Creation (GLA Stress Test) ---

def create_real_gla_large_instance() -> MinimalData:
    # 1. TIME SETUP
    shift_start, shift_end = time(9, 0), time(17, 0)
    lunch = calculate_lunch_break(shift_start, shift_end)
    slots = generate_time_slots(
        working_days=[0, 1, 2, 3, 4],
        day_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        shift_start=shift_start, shift_end=shift_end,
        slot_duration_minutes=50, break_periods=lunch
    )

    # 2. SECTIONS (52 total)
    sections = [f"CS-3{s}" for s in string.ascii_uppercase[:26]] + \
               [f"CS-3A{s}" for s in string.ascii_uppercase[:26]]
    # Truncated list for quicker API response if needed, but keeping logic for 52
    
    # 3. FACULTY LIST (100 Profs)
    faculty = [f"Prof. {string.ascii_uppercase[i%26]}{i}" for i in range(100)]
    
    # 4. SUBJECT METADATA
    theory_subjects = ["OS", "DBMS", "Automata", "Programming", "Quant", "Logic", "ImgProc"]
    lab_subjects = ["OS Lab", "DBMS Lab", "ImgProc Lab"]
    
    subject_types = {s: "THEORY" for s in theory_subjects}
    subject_types.update({s: "LAB" for s in lab_subjects})
    
    subject_durations = {s: 1 for s in theory_subjects}
    subject_durations.update({s: 2 for s in lab_subjects})

    # 5. COMPETENCY (Randomized for demo)
    # Each subject has 15-20 qualified professors
    competencies = {sub: random.sample(faculty, k=20) for sub in theory_subjects + lab_subjects}

    # 6. ROOMS (80 Theory + 30 Labs)
    theory_rooms = [f"AB1-{101+i}" for i in range(80)]
    lab_rooms = [f"LAB-{i+1}" for i in range(30)]
    rooms = theory_rooms + lab_rooms
    room_types = {r: "THEORY" for r in theory_rooms}
    room_types.update({r: "LAB" for r in lab_rooms})

    # 7. SECTION LOAD
    # Every section takes 4 random theory subjects + 2 random labs
    user_hours = {}
    for sec in sections:
        credits = {}
        for sub in random.sample(theory_subjects, 4): credits[sub] = 3
        for sub in random.sample(lab_subjects, 2): credits[sub] = 2 
        user_hours[sec] = credits

    return MinimalData(
        sections=sections, subjects=theory_subjects+lab_subjects, slots=slots,
        faculty=faculty, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        competencies=competencies, unavailability={}, hours=user_hours,
        scheduling_style="COMPACT"
    )

# --- 4. SOLVER LOGIC ---

def solve_timetable():
    data = create_real_gla_large_instance()
    model = cp_model.CpModel()
    
    # Variables
    assign = {}      # assign[(sec, sub, slot)] -> bool
    is_start = {}    # is_start[(sec, sub, slot)] -> bool (for multi-slot blocks)
    assign_room = {} # assign_room[(sec, sub, room, slot)] -> bool
    fac_assign = {}  # fac_assign[(sec, sub, faculty)] -> bool

    slots_by_day = {}
    for idx, s in enumerate(data.slots):
        slots_by_day.setdefault(s.day_index, []).append(idx)

    # --- 1. Variable Creation & Basic Linking ---
    for sec in data.sections:
        for sub in data.hours[sec].keys():
            # A. Faculty Assignment (Pick 1 qualified prof per subject per section)
            qualified = data.competencies.get(sub, [])
            if not qualified: continue # Skip if no faculty
            
            for fac in qualified:
                fac_assign[(sec, sub, fac)] = model.NewBoolVar(f"f_{sec}_{sub}_{fac}")
            model.Add(sum(fac_assign[(sec, sub, fac)] for fac in qualified) == 1)

            # B. Slot & Room Assignment
            sub_type = data.subject_types[sub]
            valid_rooms = [r for r in data.rooms if data.room_types[r] == sub_type]
            
            for s_idx in range(data.num_slots):
                assign[(sec, sub, s_idx)] = model.NewBoolVar(f"as_{sec}_{sub}_{s_idx}")
                is_start[(sec, sub, s_idx)] = model.NewBoolVar(f"st_{sec}_{sub}_{s_idx}")
                
                # Room Link: Assigned iff exactly one room is chosen
                for r in valid_rooms:
                    assign_room[(sec, sub, r, s_idx)] = model.NewBoolVar(f"asr_{sec}_{sub}_{r}_{s_idx}")
                
                model.Add(assign[(sec, sub, s_idx)] == sum(assign_room[(sec, sub, r, s_idx)] for r in valid_rooms))

    # --- 2. Hard Constraints ---
    
    # Room Clash: A room can hold max 1 class at a time
    for r in data.rooms:
        for s_idx in range(data.num_slots):
            room_usage = [assign_room[(sec, sub, r, s_idx)] for sec in data.sections 
                          for sub in data.hours[sec].keys() if (sec, sub, r, s_idx) in assign_room]
            if room_usage: model.AddAtMostOne(room_usage)

    # Faculty Clash: A prof can teach max 1 class at a time
    for fac in data.faculty:
        for s_idx in range(data.num_slots):
            fac_usage = []
            for sec in data.sections:
                for sub in data.hours[sec].keys():
                    if fac in data.competencies.get(sub, []):
                        # Boolean AND: Assigned to this slot AND Assigned to this Prof
                        is_busy = model.NewBoolVar(f"b_{fac}_{sec}_{sub}_{s_idx}")
                        model.AddBoolAnd([assign[(sec, sub, s_idx)], fac_assign[(sec, sub, fac)]]).OnlyEnforceIf(is_busy)
                        model.AddBoolOr([assign[(sec, sub, s_idx)].Not(), fac_assign[(sec, sub, fac)].Not()]).OnlyEnforceIf(is_busy.Not())
                        fac_usage.append(is_busy)
            if fac_usage: model.AddAtMostOne(fac_usage)

    # Section Clash: Max 1 subject per section per slot
    for sec in data.sections:
        for s_idx in range(data.num_slots):
            model.AddAtMostOne(assign[(sec, sub, s_idx)] for sub in data.hours[sec].keys())

    # Credit Hours & Duration Logic
    for sec in data.sections:
        for sub, credits in data.hours[sec].items():
            # Total starts = Total credits (weekly count)
            model.Add(sum(is_start[(sec, sub, s)] for s in range(data.num_slots)) == credits)
            
            duration = data.subject_durations.get(sub, 1)
            
            if duration == 2: # Lab Logic
                for s in range(data.num_slots):
                    if s == 0: 
                        model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])
                    else: 
                        # Occupied if started now OR started previous slot
                        model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)] + is_start[(sec, sub, s-1)])
                # Cannot start at last slot of day
                for day_idx, indices in slots_by_day.items():
                    model.Add(is_start[(sec, sub, indices[-1])] == 0)
            else: # Theory Logic
                for s in range(data.num_slots):
                    model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])

    # --- 3. Objective Function (Student Happiness & Optimization) ---
    obj_vars = []
    
    for sec in data.sections:
        for day_idx, indices in slots_by_day.items():
            # "is_occ[s]" = Is section busy at slot s?
            is_occ = {s: model.NewBoolVar(f"o_{sec}_{s}") for s in indices}
            for s in indices:
                model.AddMaxEquality(is_occ[s], [assign[(sec, sub, s)] for sub in data.hours[sec].keys()])
            
            daily_sum = sum(is_occ[s] for s in indices)
            is_active = model.NewBoolVar(f"active_{sec}_{day_idx}")
            model.Add(daily_sum >= 1).OnlyEnforceIf(is_active)
            model.Add(daily_sum == 0).OnlyEnforceIf(is_active.Not())

            # A. Minimize Gaps (The "Sandwich" Penalty)
            for i, s_idx in enumerate(indices):
                # Prefer morning slots (fill from start)
                obj_vars.append(is_occ[s_idx] * (i * 10)) 
                
                # Gap Penalty
                gap = model.NewBoolVar(f"gap_{sec}_{s_idx}")
                # Logic: If active day AND slot empty, potential gap penalty
                # Simplified: Just penalize empty slots in middle of day? 
                # Better: Use simple weight to push classes to start
                pass 

    model.Minimize(sum(obj_vars))

    # --- 4. Solve ---
    solver = cp_model.CpSolver()
    # OPTIMIZATION: 30 seconds is enough for a "Good" solution. 
    # 600s is too long for web.
    solver.parameters.max_time_in_seconds = 300.0 
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)

    # --- 5. Extract Data for Frontend ---
    output_data = []

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print(f"✅ Solver Status: {solver.StatusName(status)}")
        
        for sec in data.sections:
            for sub in data.hours[sec].keys():
                # 1. Which Professor?
                assigned_prof = "Staff"
                qualified = data.competencies.get(sub, [])
                for fac in qualified:
                    if solver.Value(fac_assign[(sec, sub, fac)]) == 1:
                        assigned_prof = fac
                        break
                
                # 2. Which Slots?
                for idx, slot in enumerate(data.slots):
                    if solver.Value(assign[(sec, sub, idx)]) == 1:
                        # 3. Which Room?
                        assigned_room = "TBA"
                        sub_type = data.subject_types[sub]
                        valid_rooms = [r for r in data.rooms if data.room_types[r] == sub_type]
                        for r in valid_rooms:
                            if (sec, sub, r, idx) in assign_room and solver.Value(assign_room[(sec, sub, r, idx)]) == 1:
                                assigned_room = r
                                break
                        
                        # Add to flat list
                        output_data.append({
                            "id": f"{sec}-{sub}-{idx}",
                            "section": sec,
                            "day": slot.day_name,
                            "time": slot.start_time.strftime("%H:%M"),
                            "subject": sub,
                            "teacher": assigned_prof,
                            "room": assigned_room,
                            "credits": data.subject_durations.get(sub, 1)
                        })
    else:
        print("❌ No feasible solution found.")
        return []

    return output_data