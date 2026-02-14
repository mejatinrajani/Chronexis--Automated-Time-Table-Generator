import os 
import sys
import django

# 1. FIX: Ensure project_root correctly points to the 'timetable' folder 
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, "../../"))
sys.path.append(project_root)   

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timetable.settings")
django.setup()

# 2. FIX: Group all imports together AFTER django.setup()
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import time, timedelta, datetime
from scheduler.slots.models import Slot

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
    assignments: Dict[str, Dict[str, str]]
    hours: Dict[str, Dict[str, int]]
    scheduling_style: str

    @property
    def num_slots(self):
        return len(self.slots)

def generate_time_slots(
    working_days: List[int],
    day_names: List[str],
    shift_start: time,
    shift_end: time,
    slot_duration_minutes: int = 50, # Adjusted to match your college instance
    break_periods: List[Tuple[time, time]] = None,
    buffer_minutes: int = 0,
    min_slot_gap_minutes: int = 0
) -> List[Slot]:
    if break_periods is None:
        break_periods = []

    all_slots = []
    current_date = datetime(2000, 1, 3)

    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        
        # FIX: Initialize current_time explicitly at the start of each day
        current_time = datetime.combine(current_date, shift_start)
        slot_index = 0

        while current_time.time() < shift_end:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)

            # FIX: Prevent slots from spilling over the shift_end
            if slot_end.time() > shift_end:
                break

            # Check if this slot overlaps with any break
            overlaps_break = False
            for break_start, break_end in break_periods:
                if not (slot_end.time() <= break_start or current_time.time() >= break_end):
                    overlaps_break = True
                    # FIX: If we hit a break, move the current_time to the end of that break
                    current_time = datetime.combine(current_date, break_end)
                    break

            if overlaps_break:
                continue

            slot = Slot(
                day_index=day_idx,
                day_name=day_name,
                slot_index=slot_index,
                start_time=current_time.time(),
                end_time=slot_end.time(),
                duration_minutes=slot_duration_minutes
            )
            all_slots.append(slot)
            slot_index += 1

            # FIX: Always update current_time at the end of the loop
            current_time = slot_end + timedelta(minutes=buffer_minutes + min_slot_gap_minutes)

    return all_slots


def calculate_lunch_break(shift_start: time, shift_end: time, duration_minutes: int = 60) -> List[Tuple[time, time]]:
    """
    Calculates a lunch break near the midpoint of the shift.
    Ensures lunch does not start before 12:00 PM.
    """
    # Convert times to datetime for calculation
    dummy_date = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy_date, shift_start)
    end_dt = datetime.combine(dummy_date, shift_end)
    
    # Find the mathematical midpoint
    total_seconds = (end_dt - start_dt).total_seconds()
    midpoint_dt = start_dt + timedelta(seconds=total_seconds / 2)
    
    # Rule: Lunch shouldn't start before 12:00 PM
    earliest_lunch = datetime.combine(dummy_date, time(12, 0))
    
    # Target lunch start is either the midpoint or 12:00 PM, whichever is later
    lunch_start_dt = max(midpoint_dt - timedelta(minutes=duration_minutes / 2), earliest_lunch)
    
    # Standardize to the nearest hour or half-hour for a "clean" schedule
    if lunch_start_dt.minute < 15:
        lunch_start_dt = lunch_start_dt.replace(minute=0)
    elif lunch_start_dt.minute < 45:
        lunch_start_dt = lunch_start_dt.replace(minute=30)
    else:
        lunch_start_dt = (lunch_start_dt + timedelta(hours=1)).replace(minute=0)

    lunch_end_dt = lunch_start_dt + timedelta(minutes=duration_minutes)
    
    return [(lunch_start_dt.time(), lunch_end_dt.time())]

# --- 2. THE PRODUCTION ENGINE ---
def solve_minimal_timetable(data: MinimalData):
    model = cp_model.CpModel()
    assign = {}        # (sec, sub, slot)
    is_start = {}      # (sec, sub, slot)
    assign_room = {}   # (sec, sub, room, slot)

    # Pre-calculate slot mapping
    slots_by_day = {}
    for idx, s in enumerate(data.slots):
        if s.day_index not in slots_by_day: slots_by_day[s.day_index] = []
        slots_by_day[s.day_index].append(idx)

    # --- 1. Variable Creation & Room Linking ---
    for sec in data.sections:
        for sub in data.assignments[sec].keys():
            sub_type = data.subject_types[sub]
            valid_rooms = [r for r in data.rooms if data.room_types[r] == sub_type]
            
            for slot_idx in range(data.num_slots):
                assign[(sec, sub, slot_idx)] = model.NewBoolVar(f"as_{sec}_{sub}_{slot_idx}")
                is_start[(sec, sub, slot_idx)] = model.NewBoolVar(f"st_{sec}_{sub}_{slot_idx}")
                
                for r in valid_rooms:
                    assign_room[(sec, sub, r, slot_idx)] = model.NewBoolVar(f"asr_{sec}_{sub}_{r}_{slot_idx}")
                
                # LINK: Subject active IF in exactly one valid room
                model.Add(assign[(sec, sub, slot_idx)] == sum(assign_room[(sec, sub, r, slot_idx)] for r in valid_rooms))

    # --- 2. Hard Constraints ---
    for sec in data.sections:
        # A. Section Conflict: One subject at a time
        for slot_idx in range(data.num_slots):
            model.AddAtMostOne(assign[(sec, sub, slot_idx)] for sub in data.assignments[sec].keys())

        # B. Weekly Hours and Continuity (The Atomic Lab Logic)
        for sub, credits in data.hours[sec].items():
            duration = data.subject_durations.get(sub, 1)
            num_sessions = credits # User-assigned credits = Number of sessions
            
            # 1. Total session starts must equal credits
            model.Add(sum(is_start[(sec, sub, s)] for s in range(data.num_slots)) == num_sessions)

            if duration == 2:
                # 2. THE ATOMIC COUPLING
                # Slot 's' is active ONLY IF a block started at 's' OR 's-1'
                for s in range(data.num_slots):
                    if s == 0:
                        model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])
                    else:
                        model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)] + is_start[(sec, sub, s-1)])

                # 3. DAY BOUNDARY & LUNCH SAFETY
                # A 2-hour lab cannot start in the last slot of any day
                for day_idx, indices in slots_by_day.items():
                    last_slot_of_day = indices[-1]
                    model.Add(is_start[(sec, sub, last_slot_of_day)] == 0)

                    # 4. NO REPEAT RULE: Max one 2-hour session of THIS subject per day
                    model.Add(sum(is_start[(sec, sub, s_idx)] for s_idx in indices) <= 1)

                # 5. ROOM CONTINUITY: Stay in the same room for the full 2 hours
                valid_rooms = [r for r in data.rooms if data.room_types[r] == data.subject_types[sub]]
                for s in range(data.num_slots - 1):
                    # Ensure we don't apply this rule across a day break or lunch break
                    if data.slots[s].day_index == data.slots[s+1].day_index:
                        for r in valid_rooms:
                            # If a session starts at s, Room(s) must be Room(s+1)
                            model.Add(assign_room[(sec, sub, r, s)] == assign_room[(sec, sub, r, s+1)]).OnlyEnforceIf(is_start[(sec, sub, s)])
            else:
                # THEORY RULE: 1 credit = 1 hour session
                for s in range(data.num_slots):
                    model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])
                model.Add(sum(assign[(sec, sub, s)] for s in range(data.num_slots)) == num_sessions)

            # C. PROFESSIONAL DISTRIBUTION: Max 2 classes of same subject per day
            for day_idx, day_indices in slots_by_day.items():
                model.Add(sum(is_start[(sec, sub, s_idx)] for s_idx in day_indices) <= 2)

    # --- 3. Resource Constraints ---
    # Faculty Conflict: One teacher, one place
    for fac in data.faculty:
        for s_idx in range(data.num_slots):
            fac_usage = [assign[(sec, sub, s_idx)] for sec in data.sections 
                         for sub, f in data.assignments[sec].items() if f == fac]
            if fac_usage: model.AddAtMostOne(fac_usage)

    # Room Conflict: One room, one section
    for r in data.rooms:
        for s_idx in range(data.num_slots):
            room_usage = [assign_room[(sec, sub, r, s_idx)] for sec in data.sections 
                          for sub in data.assignments[sec].keys() if (sec, sub, r, s_idx) in assign_room]
            if room_usage: model.AddAtMostOne(room_usage)

# --- 4. Optimization (The Student-First Logic) ---
    obj_vars = []
    for sec in data.sections:
        for day_idx, indices in slots_by_day.items():
            # Boolean: Is the section in college today?
            active = model.NewBoolVar(f"active_{sec}_{day_idx}")
            daily_sum = sum(assign[(sec, sub, s)] for sub in data.assignments[sec].keys() for s in indices)
            model.Add(daily_sum == 0).OnlyEnforceIf(active.Not())
            model.Add(daily_sum >= 3).OnlyEnforceIf(active) # Forced Minimum: If you come, you have at least 3 hours

            # Reward empty days (Incentivize 3-4 day weeks instead of 5 thin days)
            obj_vars.append(active * 500) 

            # --- THE GAP KILLER LOGIC ---
            # For each day, find the span between the first and last class
            for i, s_idx in enumerate(indices):
                is_occ = model.NewBoolVar(f"occ_{sec}_{s_idx}")
                model.AddMaxEquality(is_occ, [assign[(sec, sub, s_idx)] for sub in data.assignments[sec].keys()])
                
                # Penalty 1: Finish early (same as before, but lower weight)
                obj_vars.append(is_occ * (i * 20))

                # Penalty 2: THE GAP PENALTY
                # If a slot is FREE but the day is ACTIVE, apply a massive penalty
                is_free = model.NewBoolVar(f"free_{sec}_{s_idx}")
                model.Add(is_free == 1 - is_occ)
                
                # "Gap" defined as: Day is active AND this slot is free
                is_gap = model.NewBoolVar(f"gap_{sec}_{s_idx}")
                model.AddBoolAnd([active, is_free]).OnlyEnforceIf(is_gap)
                
                # Apply high penalty to gaps before the 6th slot (the core teaching day)
                if i < 6:
                    obj_vars.append(is_gap * 1000) 

    model.Minimize(sum(obj_vars))

    # --- 5. Solver Setup ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0 # Increase time for complex optimization
    solver.parameters.num_search_workers = 8 
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("\n" + "═"*80)
        print(f" SUCCESS: {solver.StatusName(status)} TIMETABLE GENERATED ".center(80, "═"))
        print("═"*80)

        # A. Section-wise Timetable (Printing only first 2 for brevity, change to data.sections for all)
        for sec in data.sections[:25]: 
            print(f"\n»»» SCHEDULE FOR SECTION: {sec} «««")
            
            for day_idx in sorted(slots_by_day.keys()):
                day_slots = slots_by_day[day_idx]
                day_name = data.slots[day_slots[0]].day_name
                
                print(f"\n  [{day_name.upper()}]")
                print(f"  {'Time Range':<18} | {'Subject':<15} | {'Faculty':<20} | {'Room'}")
                print(f"  {'-'*75}")

                last_time = data.slots[day_slots[0]].start_time
                for idx in day_slots:
                    s = data.slots[idx]
                    
                    # Detect Lunch/Break Gaps
                    if s.start_time > last_time:
                        print(f"  {last_time.strftime('%H:%M')} - {s.start_time.strftime('%H:%M')} | {'[ BREAK ]':<15} | {'-'*20} | -")

                    subj_name, fac_name, room_name = "[ FREE ]", "-", "-"
                    
                    for sub in data.assignments[sec].keys():
                        if solver.Value(assign[(sec, sub, idx)]) == 1:
                            subj_name = sub
                            fac_name = data.assignments[sec][sub]
                            # Find which room was assigned to this specific slot
                            sub_type = data.subject_types[sub]
                            valid_rooms = [r for r in data.rooms if data.room_types[r] == sub_type]
                            for r in valid_rooms:
                                if (sec, sub, r, idx) in assign_room and solver.Value(assign_room[(sec, sub, r, idx)]) == 1:
                                    room_name = r
                                    break
                            break
                    
                    print(f"  {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')} | {subj_name:<15} | {fac_name:<20} | {room_name}")
                    last_time = s.end_time

        # B. Faculty Load Verification (THE "PRO" CHECK)
        print("\n" + "═"*80)
        print(" FACULTY WORKLOAD SUMMARY ".center(80, "═"))
        faculty_hours = {f: 0 for f in data.faculty}
        for (sec, sub, idx), var in assign.items():
            if solver.Value(var) == 1:
                f = data.assignments[sec][sub]
                faculty_hours[f] += 1 # Each slot is 1 hour (approx)

        print(f"\n  {'Faculty Name':<25} | {'Total Hours/Week'}")
        print(f"  {'-'*45}")
        for fac, hrs in sorted(faculty_hours.items(), key=lambda x: x[1], reverse=True):
            if hrs > 0:
                print(f"  {fac:<25} | {hrs} slots")
        
        print("\n" + "═"*80)
    else:
        print("\n" + "!"*80)
        print(" ERROR: NO FEASIBLE SOLUTION FOUND ".center(80, "!"))
        print("!"*80)

def create_realistic_large_instance(style: str = "RELAXED") -> MinimalData:
    shift_start, shift_end = time(9, 0), time(17, 0)
    auto_breaks = calculate_lunch_break(shift_start, shift_end, duration_minutes=60)
    
    slots = generate_time_slots(
        working_days=[0, 1, 2, 3, 4],
        day_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        shift_start=shift_start, shift_end=shift_end,
        slot_duration_minutes=50, break_periods=auto_breaks,
    )

    # 1. Rooms: 60 theory + 15 labs
    theory_rooms = [f"AB{b}-{100+i}" for b in [1, 2, 3] for i in range(1, 21)]
    lab_rooms = [f"LAB-{i:02d}" for i in range(1, 16)]
    rooms = theory_rooms + lab_rooms
    room_types = {r: "THEORY" for r in theory_rooms}
    room_types.update({r: "LAB" for r in lab_rooms})

    # 2. Harder Faculty Pool (50 teachers for 25 sections)
    faculty = [f"Professor {i}" for i in range(1, 51)]

    # 3. Subjects
    theory_subjects = ["OS", "DBMS", "CN", "DAA", "AI", "Math", "SE", "TOC"]
    lab_subjects = ["OS Lab", "DBMS Lab", "CN Lab", "Python Lab", "ML Lab"]
    
    subject_types = {s: "THEORY" for s in theory_subjects}
    subject_types.update({s: "LAB" for s in lab_subjects})
    subject_durations = {s: 1 for s in theory_subjects}
    subject_durations.update({s: 2 for s in lab_subjects})

    import string, random
    random.seed(42) # Consistent hard test
    sections = list(string.ascii_uppercase[:25])

    user_assignments, user_hours = {}, {}

    for sec in sections:
        # Hard requirement: 4 Theory + 2 Labs per section
        sec_theory = random.sample(theory_subjects, k=4)
        sec_labs = random.sample(lab_subjects, k=2)
        
        assignments, credits = {}, {}
        
        for sub in sec_theory:
            assignments[sub] = random.choice(faculty)
            credits[sub] = 3 # 3 sessions of 1 hour
        for sub in sec_labs:
            assignments[sub] = random.choice(faculty)
            credits[sub] = 2 # 2 sessions of 2 hours
            
        user_assignments[sec] = assignments
        user_hours[sec] = credits

    return MinimalData(
        sections=sections, subjects=theory_subjects + lab_subjects,
        slots=slots, faculty=faculty, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        assignments=user_assignments, hours=user_hours, scheduling_style=style
    )

if __name__ == "__main__":
    data = create_realistic_large_instance()
    solve_minimal_timetable(data)   